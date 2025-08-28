from openai import OpenAI

api_key = "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"
client = OpenAI(api_key = api_key)

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    temperature=0.1,
    messages=[
        {"role":"system", "content":"You are a helpful assistant."},
        {"role":"user", "content":"2022년 월드컵 우승 팀은 어디야? "},
    ]
)

print(response)
print('----')
print(response.choices[0].message.content)