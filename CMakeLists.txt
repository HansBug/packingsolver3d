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
add_subdirectory(upstream/packingsolver EXCLUDE_FROM_ALL)

# Upstream pins the static MSVC runtime for its command line tools.  An
# extension module has to use the DLL runtime CPython itself links against, so
# every target underneath the submodule (FetchContent dependencies included)
# is switched over here rather than by patching upstream.
if(MSVC)
    function(ps3d_use_dll_runtime dir)
        get_property(targets DIRECTORY "${dir}" PROPERTY BUILDSYSTEM_TARGETS)
        foreach(target IN LISTS targets)
            get_target_property(type "${target}" TYPE)
            if(NOT type STREQUAL "INTERFACE_LIBRARY")
                set_target_properties("${target}" PROPERTIES
                    MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")
            endif()
        endforeach()
        get_property(subdirs DIRECTORY "${dir}" PROPERTY SUBDIRECTORIES)
        foreach(subdir IN LISTS subdirs)
            ps3d_use_dll_runtime("${subdir}")
        endforeach()
    endfunction()
    ps3d_use_dll_runtime("${CMAKE_CURRENT_SOURCE_DIR}/upstream/packingsolver")
endif()

# Development.Module, not Development: manylinux images ship no libpython.
set(PYBIND11_FINDPYTHON ON)
find_package(Python 3.7 COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(_core MODULE packingsolver3d/_core.cpp)
target_link_libraries(_core PRIVATE PackingSolver::box PackingSolver::boxstacks)
if(MSVC)
    set_target_properties(_core PROPERTIES
        MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")
endif()
