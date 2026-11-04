fn difference(a: i32, b: i32) -> i32 { return a - b; }
fn unused(a: i32) -> i32 { return -a; }
export "ge_compute" fn compute(a: i32, b: i32) -> i32 {
    var value: i32 = difference(a, b);
    let positive: bool = value > 0 && !(b == 0 || a == 0);
    if positive { value = value * b; } else { value = -value; }
    return value + a;
}
export "ge_min" fn minimum() -> i32 { return -2147483648; }
export "ge_three" fn three() -> i32 { return 1 + 2; }
