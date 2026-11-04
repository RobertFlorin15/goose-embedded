// Candidate first target subset: scalar C ABI; no main, allocation or I/O.
export "ge_add" fn add(a: i32, b: i32) -> i32 {
    return a + b;
}
