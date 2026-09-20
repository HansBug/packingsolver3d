// In-process bridge to PackingSolver's box and boxstacks solvers.
//
// The module exposes exactly two functions.  Each takes plain Python values
// (dicts and lists), builds the upstream instance through InstanceBuilder,
// runs optimize(), and copies the best solution back out as plain Python
// values.  No upstream object outlives the call, which keeps every C++
// lifetime on this side of the boundary.

#include <exception>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <chrono>
#include <algorithm>
#include <atomic>
#include <tuple>
#include <memory>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <array>
#include <cstdint>
#include <sstream>
#include <stdexcept>
#include <string>

#include "packingsolver/box/instance_builder.hpp"
#include "packingsolver/box/optimize.hpp"
#include "packingsolver/boxstacks/instance_builder.hpp"
#include "packingsolver/boxstacks/optimize.hpp"
#include "packingsolver/algorithms/truck.hpp"

namespace py = pybind11;

namespace {

using packingsolver::BinPos;
using packingsolver::BinTypeId;
using packingsolver::ItemPos;
using packingsolver::ItemTypeId;
using packingsolver::Length;

// Parse one of upstream's own textual tokens ("bin-packing", "anytime",
// "highs", ...) through the stream operator it declares for the type.
template <typename T>
T parse_token(const std::string& token, const char* what)
{
    std::stringstream stream(token);
    T value;
    stream >> value;
    if (stream.fail()) {
        throw std::invalid_argument(std::string("unknown ") + what + ": '" + token + "'");
    }
    return value;
}

// Read an optional key: absent or None both mean "keep upstream's default".
template <typename T>
bool read(const py::dict& dict, const char* key, T& out)
{
    if (!dict.contains(key)) {
        return false;
    }
    py::object value = dict[key];
    if (value.is_none()) {
        return false;
    }
    out = value.cast<T>();
    return true;
}

// Placed extents of a box under a rotation, transcribed from upstream's
// ItemType::x(Rotation) / y(Rotation) / z(Rotation) tables (the two problem
// types share the enumerator order XYZ, YXZ, ZYX, YZX, XZY, ZXY).
template <typename BoxT>
std::array<Length, 3> placed_extents(const BoxT& box, int rotation)
{
    switch (rotation) {
    case 0: return {box.x, box.y, box.z};
    case 1: return {box.y, box.x, box.z};
    case 2: return {box.z, box.y, box.x};
    case 3: return {box.y, box.z, box.x};
    case 4: return {box.x, box.z, box.y};
    case 5: return {box.z, box.x, box.y};
    default: throw std::logic_error("unexpected rotation index " + std::to_string(rotation));
    }
}

// Options shared by both solvers.  The LP backend is always set explicitly:
// upstream defaults the name to CLP and the bundled build has only HiGHS.
// Upstream's log goes to the per-call stream handed in here (its own
// messages_streams hook) instead of std::cout: swapping the global stream
// buffer is not thread-safe, and calls may run concurrently.
// Hooks on a solve: progress reporting and the stagnation watchdog.
//
// Upstream calls `new_solution_callback` from AlgorithmFormatter::update_solution
// every time the incumbent improves, on whichever thread found it, and also
// when only a bound moved (update_knapsack_bound and friends).  The hook keeps
// what it last saw and acts on incumbent improvements only.  On each one it
// (1) records the time for the watchdog and (2) if a Python callable was
// given, turns the incumbent into a plain dict (a snapshot: no upstream object
// crosses over) and calls it under the GIL; a falsy return value or an
// exception stops the solve through an end boolean registered on upstream's
// timer, and the exception is kept and rethrown once optimize() has returned.
//
// The watchdog is a side thread that never touches Python: every 50 ms it
// compares the time of the last improvement with upstream's clock and flips
// its own end boolean once the patience has passed without one (and
// `stop_when_unimproved_after` seconds since the start).  The patience is
// `stop_when_unimproved_for` seconds, or, when `stop_when_unimproved_ratio`
// is given, the larger of that and `ratio` times the time of the last
// improvement: upstream's anytime searches double their queues between
// passes, so the wait for the next pass grows with the time already spent,
// and a constant patience would cut every late pass short.  With a ratio the
// watchdog also waits for a first solution (a ratio of nothing is nothing);
// the time limit alone bounds a run that never finds one.
// It is upstream's own stop signal, the same one a time limit raises; nothing
// is killed or interrupted from outside.
struct SolveHooks
{
    // Progress callback.
    py::object callback;
    bool stop_callback = false;
    std::exception_ptr error;
    std::atomic<bool> reported{false};  // read by the watchdog thread once a ratio is set
    std::tuple<std::int64_t, std::int64_t, double, double, std::string> last;

    // Stagnation watchdog.
    double unimproved_for = 0.0;    // <= 0: watchdog off
    double unimproved_after = 0.0;
    double unimproved_ratio = 0.0;  // <= 0: constant patience
    bool stop_unimproved = false;
    const optimizationtools::Timer* timer = nullptr;
    std::atomic<double> last_improvement{0.0};
    std::mutex mutex;
    std::condition_variable wake;
    bool done = false;
    std::thread thread;

    bool has_watchdog() const { return unimproved_for > 0.0; }
};

template <typename Parameters>
std::shared_ptr<SolveHooks> install_hooks(Parameters& parameters, const py::dict& options)
{
    bool has_callback = options.contains("progress_callback") && !options["progress_callback"].is_none();
    double unimproved_for = 0.0;
    read(options, "stop_when_unimproved_for", unimproved_for);
    std::shared_ptr<SolveHooks> hooks;
    if (!has_callback && unimproved_for <= 0.0) {
        return hooks;
    }
    hooks = std::make_shared<SolveHooks>();
    hooks->timer = &parameters.timer;
    if (has_callback) {
        hooks->callback = py::reinterpret_borrow<py::object>(options["progress_callback"]);
        parameters.timer.add_end_boolean(&hooks->stop_callback);
    }
    if (unimproved_for > 0.0) {
        hooks->unimproved_for = unimproved_for;
        read(options, "stop_when_unimproved_after", hooks->unimproved_after);
        read(options, "stop_when_unimproved_ratio", hooks->unimproved_ratio);
        parameters.timer.add_end_boolean(&hooks->stop_unimproved);
    }
    parameters.new_solution_callback = [&parameters, hooks](const auto& output) {
        const auto& best = output.solution_pool.best();
        const std::string& label = output.solution_pool.best_label();
        auto key = std::make_tuple(
                static_cast<std::int64_t>(best.number_of_items()),
                static_cast<std::int64_t>(best.number_of_bins()),
                static_cast<double>(best.profit()),
                static_cast<double>(best.cost()),
                label);
        if (hooks->reported && key == hooks->last) {
            return;  // only a bound moved
        }
        if (best.number_of_items() == 0) {
            return;  // a bound moved before any solution exists
        }
        hooks->reported = true;
        hooks->last = key;
        double now = parameters.timer.elapsed_time();
        hooks->last_improvement.store(now);
        if (!hooks->callback) {
            return;
        }
        py::gil_scoped_acquire acquire;
        py::dict event;
        event["time"] = now;
        event["number_of_items"] = best.number_of_items();
        event["number_of_bins"] = best.number_of_bins();
        event["profit"] = best.profit();
        event["cost"] = best.cost();
        event["label"] = label;
        try {
            py::object verdict = hooks->callback(event);
            if (!verdict.is_none() && !verdict.cast<bool>()) {
                hooks->stop_callback = true;
            }
        } catch (py::error_already_set&) {
            hooks->stop_callback = true;
            hooks->error = std::current_exception();
        }
    };
    return hooks;
}

// Start the watchdog thread, if any.  Called just before optimize().
template <typename Hooks>
void start_hooks(const Hooks& hooks)
{
    if (!hooks || !hooks->has_watchdog()) {
        return;
    }
    hooks->thread = std::thread([hooks]() {
        std::unique_lock<std::mutex> lock(hooks->mutex);
        while (!hooks->done) {
            hooks->wake.wait_for(lock, std::chrono::milliseconds(50));
            double now = hooks->timer->elapsed_time();
            double last = hooks->last_improvement.load();
            double patience = hooks->unimproved_for;
            if (hooks->unimproved_ratio > 0.0) {
                if (!hooks->reported) {
                    continue;  // relative patience: nothing to be relative to before the first solution
                }
                patience = std::max(patience, hooks->unimproved_ratio * last);
            }
            if (now >= hooks->unimproved_after && now - last >= patience) {
                hooks->stop_unimproved = true;
            }
        }
    });
}

// Once optimize() has returned: stop the watchdog, surface a callback
// exception, and record why the solve ended early, if it did.
template <typename Hooks>
void finish_hooks(const Hooks& hooks, py::dict& result)
{
    if (hooks && hooks->thread.joinable()) {
        {
            std::lock_guard<std::mutex> lock(hooks->mutex);
            hooks->done = true;
        }
        hooks->wake.notify_all();
        hooks->thread.join();
    }
    if (hooks && hooks->error) {
        std::rethrow_exception(hooks->error);
    }
    if (hooks && hooks->stop_callback) {
        result["stop_reason"] = "callback";
    } else if (hooks && hooks->stop_unimproved) {
        result["stop_reason"] = "unimproved";
    } else {
        result["stop_reason"] = py::none();
    }
}

template <typename Parameters>
void fill_common_parameters(Parameters& parameters, const py::dict& options, std::ostream& log)
{
    parameters.messages_to_stdout = false;
    parameters.messages_streams.push_back(&log);
    parameters.verbosity_level = 0;
    read(options, "verbosity_level", parameters.verbosity_level);

    double time_limit = 0.0;
    if (read(options, "time_limit", time_limit)) {
        parameters.timer.set_time_limit(time_limit);
    }
    std::int64_t memory_limit = 0;
    if (read(options, "memory_limit", memory_limit)) {
        parameters.memory_limit_megabytes = memory_limit;
    }
    std::string token;
    if (read(options, "optimization_mode", token)) {
        parameters.optimization_mode = parse_token<packingsolver::OptimizationMode>(token, "optimization mode");
    }
    if (read(options, "linear_programming_solver", token)) {
        parameters.linear_programming_solver_name
            = parse_token<columngenerationsolver::SolverName>(token, "linear programming solver");
    }
}

void set_switch(bool& flag, const py::dict& options, const char* key)
{
    bool value = false;
    if (read(options, key, value)) {
        flag = value;
    }
}

// Bin and item fields common to both builders.
template <typename Builder>
BinTypeId add_bin_type(Builder& builder, const py::dict& spec)
{
    BinTypeId bin_type_id = builder.add_bin_type(
            spec["x"].cast<Length>(), spec["y"].cast<Length>(), spec["z"].cast<Length>());
    double cost = 0.0;
    if (read(spec, "cost", cost)) {
        builder.set_bin_type_cost(bin_type_id, cost);
    }
    BinPos copies = 1;
    if (read(spec, "copies", copies)) {
        builder.set_bin_type_copies(bin_type_id, copies);
    }
    if (read(spec, "copies_min", copies)) {
        builder.set_bin_type_copies_min(bin_type_id, copies);
    }
    double maximum_weight = 0.0;
    if (read(spec, "maximum_weight", maximum_weight)) {
        builder.set_bin_type_maximum_weight(bin_type_id, maximum_weight);
    }
    return bin_type_id;
}

template <typename Builder, typename Rotation>
ItemTypeId add_item_type(Builder& builder, const py::dict& spec, Rotation (*rotation_from_string)(const std::string&))
{
    ItemTypeId item_type_id = builder.add_item_type(
            spec["x"].cast<Length>(), spec["y"].cast<Length>(), spec["z"].cast<Length>());
    double profit = 0.0;
    if (read(spec, "profit", profit)) {
        builder.set_item_type_profit(item_type_id, profit);
    }
    double weight = 0.0;
    if (read(spec, "weight", weight)) {
        builder.set_item_type_weight(item_type_id, weight);
    }
    ItemPos copies = 1;
    if (read(spec, "copies", copies)) {
        builder.set_item_type_copies(item_type_id, copies);
    }
    if (read(spec, "copies_min", copies)) {
        builder.set_item_type_copies_min(item_type_id, copies);
    }
    if (spec.contains("rotations") && !spec["rotations"].is_none()) {
        for (py::handle token : spec["rotations"].cast<py::list>()) {
            builder.add_item_type_rotation(item_type_id, rotation_from_string(token.cast<std::string>()));
        }
    }
    return item_type_id;
}

template <typename Builder>
void set_objective(Builder& builder, const py::dict& instance)
{
    std::string token;
    if (read(instance, "objective", token)) {
        builder.set_objective(parse_token<packingsolver::Objective>(token, "objective"));
    }
}

template <typename Instance>
py::dict describe_bin(const Instance& instance, BinTypeId bin_type_id, BinPos copies)
{
    const auto& bin_type = instance.bin_type(bin_type_id);
    py::dict bin;
    bin["bin_type_id"] = bin_type_id;
    bin["copies"] = copies;
    bin["x"] = bin_type.box.x;
    bin["y"] = bin_type.box.y;
    bin["z"] = bin_type.box.z;
    return bin;
}

template <typename Output>
py::dict describe_output(const Output& output, const std::ostringstream& log)
{
    py::dict result;
    result["output"] = output.to_json().dump();
    result["stdout"] = log.str();
    result["stderr"] = "";
    return result;
}

py::dict box_solve(const py::dict& instance_spec, const py::dict& options)
{
    namespace box = packingsolver::box;

    box::InstanceBuilder builder;
    set_objective(builder, instance_spec);
    for (py::handle spec : instance_spec["bins"].cast<py::list>()) {
        add_bin_type(builder, spec.cast<py::dict>());
    }
    for (py::handle spec : instance_spec["items"].cast<py::list>()) {
        add_item_type(builder, spec.cast<py::dict>(), &box::rotation_from_string);
    }
    box::Instance instance = builder.build();

    std::ostringstream log;
    box::OptimizeParameters parameters;
    fill_common_parameters(parameters, options, log);
    set_switch(parameters.use_tree_search, options, "use_tree_search");
    set_switch(parameters.use_tree_search_maximal_spaces, options, "use_tree_search_maximal_spaces");
    set_switch(parameters.use_sequential_single_knapsack, options, "use_sequential_single_knapsack");
    set_switch(parameters.use_sequential_value_correction, options, "use_sequential_value_correction");
    set_switch(parameters.use_column_generation, options, "use_column_generation");
    set_switch(parameters.use_dichotomic_search, options, "use_dichotomic_search");
    set_switch(parameters.use_dual_feasible_functions, options, "use_dual_feasible_functions");
    auto hooks = install_hooks(parameters, options);
    start_hooks(hooks);

    box::Output output = [&]() {
        py::gil_scoped_release release;
        return box::optimize(instance, parameters);
    }();

    const box::Solution& solution = output.solution_pool.best();
    py::list bins;
    for (BinPos bin_pos = 0; bin_pos < solution.number_of_different_bins(); ++bin_pos) {
        const box::SolutionBin& solution_bin = solution.bin(bin_pos);
        py::dict bin = describe_bin(instance, solution_bin.bin_type_id, solution_bin.copies);
        py::list placements;
        for (const box::SolutionItem& item : solution_bin.items) {
            const auto& item_type = instance.item_type(item.item_type_id);
            std::array<Length, 3> extents = placed_extents(item_type.box, static_cast<int>(item.rotation));
            py::dict placement;
            placement["item_type_id"] = item.item_type_id;
            placement["x"] = item.bl_corner.x;
            placement["y"] = item.bl_corner.y;
            placement["z"] = item.bl_corner.z;
            placement["lx"] = extents[0];
            placement["ly"] = extents[1];
            placement["lz"] = extents[2];
            placement["rotation"] = box::to_string(item.rotation);
            placements.append(placement);
        }
        bin["placements"] = placements;
        bin["stacks"] = py::list();
        bins.append(bin);
    }

    py::dict result = describe_output(output, log);
    finish_hooks(hooks, result);
    result["bins"] = bins;
    return result;
}

py::dict boxstacks_solve(const py::dict& instance_spec, const py::dict& options)
{
    namespace boxstacks = packingsolver::boxstacks;

    boxstacks::InstanceBuilder builder;
    set_objective(builder, instance_spec);
    std::string token;
    if (read(instance_spec, "unloading_constraint", token)) {
        builder.set_unloading_constraint(
                parse_token<packingsolver::rectangle::UnloadingConstraint>(token, "unloading constraint"));
    }
    for (py::handle handle : instance_spec["bins"].cast<py::list>()) {
        py::dict spec = handle.cast<py::dict>();
        BinTypeId bin_type_id = add_bin_type(builder, spec);
        double maximum_stack_density = 0.0;
        if (read(spec, "maximum_stack_density", maximum_stack_density)) {
            builder.set_bin_type_maximum_stack_density(bin_type_id, maximum_stack_density);
        }
        if (spec.contains("semi_trailer_truck") && !spec["semi_trailer_truck"].is_none()) {
            py::dict truck_spec = spec["semi_trailer_truck"].cast<py::dict>();
            packingsolver::SemiTrailerTruckData truck;
            truck.is = true;
            read(truck_spec, "tractor_weight", truck.tractor_weight);
            read(truck_spec, "front_axle_middle_axle_distance", truck.front_axle_middle_axle_distance);
            read(truck_spec, "front_axle_tractor_gravity_center_distance", truck.front_axle_tractor_gravity_center_distance);
            read(truck_spec, "front_axle_harness_distance", truck.front_axle_harness_distance);
            read(truck_spec, "empty_trailer_weight", truck.empty_trailer_weight);
            read(truck_spec, "harness_rear_axle_distance", truck.harness_rear_axle_distance);
            read(truck_spec, "trailer_gravity_center_rear_axle_distance", truck.trailer_gravity_center_rear_axle_distance);
            read(truck_spec, "trailer_start_harness_distance", truck.trailer_start_harness_distance);
            read(truck_spec, "rear_axle_maximum_weight", truck.rear_axle_maximum_weight);
            read(truck_spec, "middle_axle_maximum_weight", truck.middle_axle_maximum_weight);
            builder.set_bin_type_semi_trailer_truck_parameters(bin_type_id, truck);
        }
    }
    if (instance_spec.contains("defects") && !instance_spec["defects"].is_none()) {
        for (py::handle handle : instance_spec["defects"].cast<py::list>()) {
            py::dict spec = handle.cast<py::dict>();
            builder.add_defect(
                    spec["bin_type_id"].cast<BinTypeId>(),
                    spec["x"].cast<Length>(), spec["y"].cast<Length>(),
                    spec["lx"].cast<Length>(), spec["ly"].cast<Length>());
        }
    }
    for (py::handle handle : instance_spec["items"].cast<py::list>()) {
        py::dict spec = handle.cast<py::dict>();
        ItemTypeId item_type_id = add_item_type(builder, spec, &boxstacks::rotation_from_string);
        packingsolver::GroupId group_id = 0;
        if (read(spec, "group_id", group_id)) {
            builder.set_item_type_group(item_type_id, group_id);
        }
        packingsolver::StackabilityId stackability_id = 0;
        if (read(spec, "stackability_id", stackability_id)) {
            builder.set_item_type_stackability_id(item_type_id, stackability_id);
        }
        Length nesting_height = 0;
        if (read(spec, "nesting_height", nesting_height)) {
            builder.set_item_type_nesting_height(item_type_id, nesting_height);
        }
        ItemPos maximum_stackability = 0;
        if (read(spec, "maximum_stackability", maximum_stackability)) {
            builder.set_item_type_maximum_stackability(item_type_id, maximum_stackability);
        }
        double maximum_weight_above = 0.0;
        if (read(spec, "maximum_weight_above", maximum_weight_above)) {
            builder.set_item_type_maximum_weight_above(item_type_id, maximum_weight_above);
        }
    }
    boxstacks::Instance instance = builder.build();

    std::ostringstream log;
    boxstacks::OptimizeParameters parameters;
    fill_common_parameters(parameters, options, log);
    auto hooks = install_hooks(parameters, options);
    start_hooks(hooks);

    boxstacks::Output output = [&]() {
        py::gil_scoped_release release;
        return boxstacks::optimize(instance, parameters);
    }();

    const boxstacks::Solution& solution = output.solution_pool.best();
    py::list bins;
    for (BinPos bin_pos = 0; bin_pos < solution.number_of_different_bins(); ++bin_pos) {
        const boxstacks::SolutionBin& solution_bin = solution.bin(bin_pos);
        py::dict bin = describe_bin(instance, solution_bin.bin_type_id, solution_bin.copies);
        py::list placements;
        py::list stacks;
        int stack_id = 0;
        for (const boxstacks::SolutionStack& solution_stack : solution_bin.stacks) {
            py::dict stack;
            stack["stack_id"] = stack_id;
            stack["x"] = solution_stack.x_start;
            stack["y"] = solution_stack.y_start;
            stack["lx"] = solution_stack.x_end - solution_stack.x_start;
            stack["ly"] = solution_stack.y_end - solution_stack.y_start;
            stack["lz"] = solution_stack.z_end;
            stacks.append(stack);
            for (const boxstacks::SolutionItem& item : solution_stack.items) {
                const auto& item_type = instance.item_type(item.item_type_id);
                std::array<Length, 3> extents = placed_extents(item_type.box, static_cast<int>(item.rotation));
                py::dict placement;
                placement["item_type_id"] = item.item_type_id;
                placement["x"] = solution_stack.x_start;
                placement["y"] = solution_stack.y_start;
                placement["z"] = item.z_start;
                placement["lx"] = extents[0];
                placement["ly"] = extents[1];
                placement["lz"] = extents[2];
                placement["rotation"] = boxstacks::to_string(item.rotation);
                placement["stack_id"] = stack_id;
                placement["group_id"] = item_type.group_id;
                placements.append(placement);
            }
            ++stack_id;
        }
        bin["placements"] = placements;
        bin["stacks"] = stacks;
        bins.append(bin);
    }

    py::dict result = describe_output(output, log);
    finish_hooks(hooks, result);
    result["bins"] = bins;
    return result;
}

}  // namespace

PYBIND11_MODULE(_core, m)
{
    m.doc() = "In-process bridge to PackingSolver's box and boxstacks solvers.";
    m.def("box_solve", &box_solve, py::arg("instance"), py::arg("options"),
          "Build a box instance from plain values, run optimize(), return the best solution as plain values.");
    m.def("boxstacks_solve", &boxstacks_solve, py::arg("instance"), py::arg("options"),
          "Build a boxstacks instance from plain values, run optimize(), return the best solution as plain values.");
}
