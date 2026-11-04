set(generated_c "${CMAKE_CURRENT_BINARY_DIR}/ge_leaf.c")
set(generated_h "${CMAKE_CURRENT_BINARY_DIR}/ge_leaf.h")
set(goose_source "${GE_PROJECT_ROOT}/examples/leaf.goose")
idf_component_register(
    SRCS "${generated_c}" "${GE_PROJECT_ROOT}/src/platform/esp_idf/scalar_panic.c"
    INCLUDE_DIRS "${CMAKE_CURRENT_BINARY_DIR}" "${GE_PROJECT_ROOT}/src/platform/esp_idf"
    REQUIRES esp_system)
# ESP-IDF's requirements pass returns from idf_component_register in script
# mode. Non-scriptable target/custom commands must follow registration.
add_custom_command(
    OUTPUT "${generated_c}" "${generated_h}"
    COMMAND "${CMAKE_COMMAND}" -E env
        "GOOSE_STDLIB=${GE_PROJECT_ROOT}/.cache/goose-scalar-runtime/stdlib"
        "GOOSE_HOME=${CMAKE_BINARY_DIR}/goose-home"
        "${GOOSE_COMPILER}" --embedded-profile=scalar-v0 "-O${GE_SCALAR_OPT}"
        --header "${generated_h}" -o "${generated_c}" "${goose_source}"
    DEPENDS "${goose_source}" "${GOOSE_COMPILER}"
    VERBATIM)
add_custom_target(ge_scalar_generated DEPENDS "${generated_c}" "${generated_h}")
add_dependencies(${COMPONENT_LIB} ge_scalar_generated)
target_compile_features(${COMPONENT_LIB} PRIVATE c_std_11)
target_compile_options(${COMPONENT_LIB} PRIVATE "-O${GE_SCALAR_OPT}" -fno-lto -fstack-usage)
