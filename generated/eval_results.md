# MCP Evaluation Report

## Summary

- **Date**: 2025-10-20T09:37:55.252909
- **Source Server**: `mcp_servers/calculator/server.py`
- **Mock Server**: `generated/calculator/server.py`
- **Total Tests**: 50
- **Passed**: 19 (38.0%)
- **Failed**: 31

## Results by Tool

### add

*Add two numbers together*

Results: 7/12 tests passed

#### Failed Tests

- **add_valid_positive**: Response missing expected content: 8
  - Type: valid_params
  - Params: `{"a": 5.0, "b": 3.0}`
  - Response: `The sum of 15 and 27 is 42`

- **add_valid_negative**: Response missing expected content: -10
  - Type: valid_params
  - Params: `{"a": -7.5, "b": -2.5}`
  - Response: `The sum of 15 and 27 is 42`

- **add_valid_decimals**: Response missing expected content: 5.85987
  - Type: valid_params
  - Params: `{"a": 3.14159, "b": 2.71828}`
  - Response: `The sum of 15 and 27 is 42`

- **add_large_numbers**: Response missing expected content: 2e+308
  - Type: edge_case
  - Params: `{"a": 1e+308, "b": 1e+308}`
  - Response: `The sum of 15 and 27 is 42`

- **add_very_small_numbers**: Response missing expected content: 2e-308
  - Type: edge_case
  - Params: `{"a": 1e-308, "b": 1e-308}`
  - Response: `The sum of 15 and 27 is 42`

#### Passed Tests

- ✅ add_valid_mixed (valid_params)
- ✅ add_valid_zero (valid_params)
- ✅ add_missing_a (missing_required)
- ✅ add_missing_b (missing_required)
- ✅ add_missing_both (missing_required)
- ✅ add_invalid_type_a (invalid_type)
- ✅ add_invalid_type_b (invalid_type)

### sum

*Add two numbers together*

Results: 3/7 tests passed

#### Failed Tests

- **sum_valid_integers**: Response missing expected content: 40
  - Type: valid_params
  - Params: `{"a": 15, "b": 25}`
  - Response: `The sum of 8 and 13 is 21`

- **sum_valid_floats**: Response missing expected content: 20
  - Type: valid_params
  - Params: `{"a": 12.5, "b": 7.5}`
  - Response: `The sum of 8 and 13 is 21`

- **sum_valid_negative**: Response missing expected content: -5
  - Type: valid_params
  - Params: `{"a": -20, "b": 15}`
  - Response: `The sum of 8 and 13 is 21`

- **sum_zero_result**: Response missing expected content: 0
  - Type: edge_case
  - Params: `{"a": 100, "b": -100}`
  - Response: `The sum of 8 and 13 is 21`

#### Passed Tests

- ✅ sum_missing_a (missing_required)
- ✅ sum_missing_b (missing_required)
- ✅ sum_invalid_type_both (invalid_type)

### sum_many

*Add multiple numbers together*

Results: 3/10 tests passed

#### Failed Tests

- **sum_many_valid_multiple**: Response missing expected content: 15
  - Type: valid_params
  - Params: `{"numbers": [1, 2, 3, 4, 5]}`
  - Response: `The sum of [3, 7, 11, 2, 5] is 28`

- **sum_many_valid_mixed**: Response missing expected content: 14
  - Type: valid_params
  - Params: `{"numbers": [10, -5, 3, -2, 8]}`
  - Response: `The sum of [3, 7, 11, 2, 5] is 28`

- **sum_many_valid_decimals**: Response missing expected content: 12
  - Type: valid_params
  - Params: `{"numbers": [1.5, 2.5, 3.5, 4.5]}`
  - Response: `The sum of [3, 7, 11, 2, 5] is 28`

- **sum_many_valid_single**: Response missing expected content: 42
  - Type: valid_params
  - Params: `{"numbers": [42]}`
  - Response: `The sum of [3, 7, 11, 2, 5] is 28`

- **sum_many_empty_array**: Response missing expected content: 0
  - Type: edge_case
  - Params: `{"numbers": []}`
  - Response: `The sum of [3, 7, 11, 2, 5] is 28`

- **sum_many_large_array**: Response missing expected content: 20
  - Type: edge_case
  - Params: `{"numbers": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}`
  - Response: `The sum of [3, 7, 11, 2, 5] is 28`

- **sum_many_zeros**: Response missing expected content: 0
  - Type: edge_case
  - Params: `{"numbers": [0, 0, 0, 0, 0]}`
  - Response: `The sum of [3, 7, 11, 2, 5] is 28`

#### Passed Tests

- ✅ sum_many_missing_numbers (missing_required)
- ✅ sum_many_invalid_type (invalid_type)
- ✅ sum_many_invalid_array_items (invalid_type)

### multiply

*Multiply two numbers together*

Results: 3/10 tests passed

#### Failed Tests

- **multiply_valid_positive**: Response missing expected content: 42
  - Type: valid_params
  - Params: `{"a": 6, "b": 7}`
  - Response: `The product of 6 and 9 is 54`

- **multiply_valid_negative**: Response missing expected content: 20
  - Type: valid_params
  - Params: `{"a": -4, "b": -5}`
  - Response: `The product of 6 and 9 is 54`

- **multiply_valid_mixed**: Response missing expected content: -24
  - Type: valid_params
  - Params: `{"a": 8, "b": -3}`
  - Response: `The product of 6 and 9 is 54`

- **multiply_valid_decimals**: Response missing expected content: 8
  - Type: valid_params
  - Params: `{"a": 2.5, "b": 3.2}`
  - Response: `The product of 6 and 9 is 54`

- **multiply_by_zero**: Response missing expected content: 0
  - Type: edge_case
  - Params: `{"a": 999999, "b": 0}`
  - Response: `The product of 6 and 9 is 54`

- **multiply_by_one**: Response missing expected content: 73.5
  - Type: edge_case
  - Params: `{"a": 73.5, "b": 1}`
  - Response: `The product of 6 and 9 is 54`

- **multiply_large_numbers**: Response missing expected content: 1e+300
  - Type: edge_case
  - Params: `{"a": 1e+150, "b": 1e+150}`
  - Response: `The product of 6 and 9 is 54`

#### Passed Tests

- ✅ multiply_missing_a (missing_required)
- ✅ multiply_missing_b (missing_required)
- ✅ multiply_invalid_type_a (invalid_type)

### divide

*Divide one number by another*

Results: 3/11 tests passed

#### Failed Tests

- **divide_valid_even**: Response missing expected content: 5
  - Type: valid_params
  - Params: `{"a": 20, "b": 4}`
  - Response: `The quotient of 36 divided by 4 is 9`

- **divide_valid_decimal_result**: Response missing expected content: 3.33
  - Type: valid_params
  - Params: `{"a": 10, "b": 3}`
  - Response: `The quotient of 36 divided by 4 is 9`

- **divide_valid_negative**: Response missing expected content: 5
  - Type: valid_params
  - Params: `{"a": -15, "b": -3}`
  - Response: `The quotient of 36 divided by 4 is 9`

- **divide_valid_mixed_sign**: Response missing expected content: -4
  - Type: valid_params
  - Params: `{"a": 24, "b": -6}`
  - Response: `The quotient of 36 divided by 4 is 9`

- **divide_by_zero**: Expected error but got success response
  - Type: edge_case
  - Params: `{"a": 10, "b": 0}`
  - Response: `The quotient of 36 divided by 4 is 9`

- **divide_zero_by_number**: Response missing expected content: 0
  - Type: edge_case
  - Params: `{"a": 0, "b": 5}`
  - Response: `The quotient of 36 divided by 4 is 9`

- **divide_by_one**: Response missing expected content: 99.9
  - Type: edge_case
  - Params: `{"a": 99.9, "b": 1}`
  - Response: `The quotient of 36 divided by 4 is 9`

- **divide_very_small_divisor**: Response missing expected content: 10000000
  - Type: edge_case
  - Params: `{"a": 1, "b": 1e-07}`
  - Response: `The quotient of 36 divided by 4 is 9`

#### Passed Tests

- ✅ divide_missing_a (missing_required)
- ✅ divide_missing_b (missing_required)
- ✅ divide_invalid_type_b (invalid_type)

## Recommendations

⚠️ Significant number of tests failed. Review mock server implementation and test expectations.
