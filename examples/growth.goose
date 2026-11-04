fn main() {
    var bytes: u8[>..] = [];
    for i in 32 { bytes.push(i as! u8); }
    assert(bytes.len == 32);
    assert(bytes[31] == 31);
    print("growth: 32");
}
