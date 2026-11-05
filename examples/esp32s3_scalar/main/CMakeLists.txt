idf_component_register(SRCS "app_main.c" "abi_checks.c" INCLUDE_DIRS "."
                       REQUIRES goose_scalar esp_rom freertos esp_app_format)
add_dependencies(${COMPONENT_LIB} ge_scalar_generated)
target_compile_features(${COMPONENT_LIB} PRIVATE c_std_11)
target_compile_options(${COMPONENT_LIB} PRIVATE "-O${GE_SCALAR_OPT}" -fno-lto -fstack-usage)
