cmake_minimum_required(VERSION 3.16)
project(App CXX)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

project(app)
add_executable(${PROJECT_NAME} main.cpp)

find_package(pkgb REQUIRED)
target_link_libraries(${PROJECT_NAME} PRIVATE pkgb)

install(TARGETS ${PROJECT_NAME} EXPORT ${PROJECT_NAME}Targets)

install(EXPORT ${PROJECT_NAME}Targets
        DESTINATION cmake/
        FILE ${PROJECT_NAME}Targets.cmake)

export(EXPORT ${PROJECT_NAME}Targets
       FILE ${PROJECT_NAME}Targets.cmake)

configure_file(Config.cmake.in ${CMAKE_BINARY_DIR}/${PROJECT_NAME}Config.cmake @ONLY)
install(FILES ${CMAKE_BINARY_DIR}/${PROJECT_NAME}Config.cmake DESTINATION cmake/)
