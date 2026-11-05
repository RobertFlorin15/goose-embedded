#ifndef GE_TEST_FREERTOS_H
#define GE_TEST_FREERTOS_H
#include <stdint.h>
#define INCLUDE_uxTaskGetStackHighWaterMark 1
#ifdef GE_TEST_WIDE_STACK
typedef uint32_t StackType_t;
#else
typedef uint8_t StackType_t;
#endif
typedef uint32_t UBaseType_t;
typedef void *TaskHandle_t;
#endif
