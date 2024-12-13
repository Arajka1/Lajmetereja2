from celery_config import add, multiply

# Testimi i funksioneve
result_add = add.delay(4, 6)
print(f"Resultati i adderes: {result_add.get()}")

result_multiply = multiply.delay(4, 6)
print(f"Resultati i shumezimit: {result_multiply.get()}")
