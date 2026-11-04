extern fn ge_foreign(value: i32) -> i32;
export "ge_call_foreign" fn call_foreign(value: i32) -> i32 {
    return ge_foreign(value);
}
