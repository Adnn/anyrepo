cmake_minimum_required(VERSION 3.16)
project(Pkga CXX)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

project(pkga)
add_library(${PROJECT_NAME} A.cpp)

find_package(Boost REQUIRED)
target_link_libraries(${PROJECT_NAME} PRIVATE Boost::boost)

set_target_properties(${PROJECT_NAME}
    PROPERTIES PUBLIC_HEADER A.h
)

target_include_directories(${PROJECT_NAME} INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    $<INSTALL_INTERFACE:include/${PROJECT_NAME}>
)

install(TARGETS ${PROJECT_NAME} EXPORT ${PROJECT_NAME}Targets
        PUBLIC_HEADER
        DESTINATION include/${PROJECT_NAME})

install(EXPORT ${PROJECT_NAME}Targets
        DESTINATION cmake/
        FILE ${PROJECT_NAME}Targets.cmake)

export(EXPORT ${PROJECT_NAME}Targets
       FILE ${PROJECT_NAME}Targets.cmake)

configure_file(Config.cmake.in ${CMAKE_BINARY_DIR}/${PROJECT_NAME}Config.cmake @ONLY)
install(FILES ${CMAKE_BINARY_DIR}/${PROJECT_NAME}Config.cmake DESTINATION cmake/)
