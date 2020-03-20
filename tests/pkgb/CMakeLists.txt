cmake_minimum_required(VERSION 3.16)
project(Pkgb CXX)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

project(pkgb)
add_library(${PROJECT_NAME} B.cpp)

find_package(pkga REQUIRED)
target_link_libraries(${PROJECT_NAME} PUBLIC pkga)

set_target_properties(${PROJECT_NAME}
    PROPERTIES PUBLIC_HEADER B.h
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

