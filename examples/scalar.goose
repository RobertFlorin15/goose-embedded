export "ge_add" fn add(a: i32, b: i32) -> i32 {
    return a + b;
}
fn main() {
    assert(add(20, 22) == 42);
    print("goose-embedded: 42");
}
