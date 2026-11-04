#ifndef GE_TEST_ESP_SYSTEM_H
#define GE_TEST_ESP_SYSTEM_H
/* Host test double only. Real builds use the pinned SDK header. */
void __attribute__((noreturn)) esp_system_abort(const char *details);
#endif
