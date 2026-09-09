cmake_minimum_required(VERSION 3.28)

project(packingsolver3d LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
# Upstream's static libraries end up inside a shared extension module.
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# The one supported upstream configuration: HiGHS as the only LP backend, no
# executables, no upstream unit tests.  Never disable both LP backends -- the
# column generation code throws at runtime otherwise.
set(PACKINGSOLVER_USE_CLP OFF CACHE BOOL "" FORCE)
set(PACKINGSOLVER_USE_HIGHS ON CACHE BOOL "" FORCE)
set(PACKINGSOLVER_USE_KNITRO OFF CACHE BOOL "" FORCE)
set(PACKINGSOLVER_BUILD_MAIN OFF CACHE BOOL "" FORCE)
set(PACKINGSOLVER_BUILD_TEST OFF CACHE BOOL "" FORCE)
# Every project() call underneath upstream (its own and its FetchContent
# dependencies) resets the default MSVC runtime to the DLL one, see the file.
set(CMAKE_PROJECT_INCLUDE "${CMAKE_CURRENT_SOURCE_DIR}/cmake/msvc_runtime.cmake")
add_subdirectory(upstream/packingsolver EXCLUDE_FROM_ALL)

# Upstream's own targets are created after its set(CMAKE_MSVC_RUNTIME_LIBRARY
# MultiThreaded), which the project() hook above cannot pre-empt, so they are
# switched to the DLL runtime by property afterwards.  Only real binary targets
# carry the property; BUILDSYSTEM_TARGETS also lists INTERFACE, IMPORTED and
# utility targets, and a name shadowed by a same-named ALIAS cannot be modified
# at all (those are covered by the hook).
set(PS3D_RUNTIME_TARGET_TYPES STATIC_LIBRARY SHARED_LIBRARY MODULE_LIBRARY OBJECT_LIBRARY EXECUTABLE)
function(ps3d_use_dll_runtime dir)
    get_property(targets DIRECTORY "${dir}" PROPERTY BUILDSYSTEM_TARGETS)
    foreach(target IN LISTS targets)
        get_target_property(aliased "${target}" ALIASED_TARGET)
        get_target_property(imported "${target}" IMPORTED)
        get_target_property(type "${target}" TYPE)
        if(NOT aliased AND NOT imported AND type IN_LIST PS3D_RUNTIME_TARGET_TYPES)
            set_target_properties("${target}" PROPERTIES
                MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")
        endif()
    endforeach()
    get_property(subdirs DIRECTORY "${dir}" PROPERTY SUBDIRECTORIES)
    foreach(subdir IN LISTS subdirs)
        ps3d_use_dll_runtime("${subdir}")
    endforeach()
endfunction()
if(MSVC)
    ps3d_use_dll_runtime("${CMAKE_CURRENT_SOURCE_DIR}/upstream/packingsolver")
endif()

# Development.Module, not Development: manylinux images ship no libpython.
set(PYBIND11_FINDPYTHON ON)
find_package(Python 3.7 COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(_core MODULE packingsolver3d/_core.cpp)
target_link_libraries(_core PRIVATE PackingSolver::box PackingSolver::boxstacks)

# Coverage of the bridge itself (not of upstream): gcov instrumentation on the
# module's own translation unit, read back with gcovr after the test run.
option(PS3D_COVERAGE "Instrument packingsolver3d/_core.cpp for gcov" OFF)
if(PS3D_COVERAGE)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(_core PRIVATE --coverage -O0)
        target_link_options(_core PRIVATE --coverage)
    else()
        message(WARNING "PS3D_COVERAGE needs GCC or Clang; ignored for ${CMAKE_CXX_COMPILER_ID}")
    endif()
endif()
if(MSVC)
    set_target_properties(_core PROPERTIES
        MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")
endif()
