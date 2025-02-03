from openai import OpenAI
import time


def evaluate_response_time(duration):
    if duration < 3:
        return "响应速度很快，系统状况良好"
    elif duration < 7:
        return "响应速度正常，可以继续调用"
    elif duration < 10:
        return "响应速度较慢，建议间隔一段时间后再调用"
    else:
        return "响应速度异常，当前系统负载可能较高，不建议继续调用"


def call_api():
    client = OpenAI(
        api_key="sk-c65073ad363a493db1121bdddf1ef931",
        base_url="https://api.deepseek.com"
    )

    start_time = time.time()

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"},
            ],
            stream=False
        )

        duration = time.time() - start_time

        print(f"响应内容: {response.choices[0].message.content}")
        print(f"响应时长: {duration:.2f} 秒")
        print(f"状态评估: {evaluate_response_time(duration)}")

        return duration

    except Exception as e:
        print(f"调用出错: {e}")
        return None


# 执行调用
call_api()