recursive fn countdown(value: i32) -> i32 {
    if value <= 0 { return 0; }
    return 1 + countdown(value - 1);
}
export "ge_countdown" fn run(value: i32) -> i32 {
    return countdown(value);
}
