# Included right after every project() call underneath upstream/packingsolver
# through CMAKE_PROJECT_INCLUDE (see the top-level CMakeLists.txt).
#
# Upstream pins the static MSVC runtime for its command line tools, and its
# FetchContent dependencies inherit that choice.  Targets created after this
# point default to the DLL runtime CPython links against.  Two dependencies
# (knapsacksolver, multiplechoicesubsetsumsolver) declare an ALIAS with the
# same name as the real library, which makes their targets unreachable by
# set_target_properties, so fixing the default at project() time is the only
# way to reach them without patching the sources.
if(MSVC)
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")
endif()
