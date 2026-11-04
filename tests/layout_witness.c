/* Freestanding 32-bit witness for upstream packed pointer + int64 layout.
   This does not test Xtensa, only the consequence of 32-bit C pointers. */
#pragma pack(push, 1)
struct slice { void *data; long long len; };
struct rref { void *hdr; void *stack; };
#pragma pack(pop)
_Static_assert(sizeof(void *) == 4, "witness requires 32-bit pointers");
_Static_assert(sizeof(long long) == 8, "witness requires 64-bit lengths");
_Static_assert(sizeof(struct slice) == 12, "32-bit packed slice is 12 bytes");
_Static_assert(sizeof(struct rref) == 8, "32-bit packed rref is 8 bytes");
