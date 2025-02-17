# create_php.py

def create_php_file():
    php_content = """
<?php
header('Content-Type: application/json');

$API_URL = "https://api.deepseek.com/v1/chat/completions";
$API_KEY = 'sk-c65073ad363a493db1121bdddf1ef931';
$MODEL_NAME = "deepseek-chat";

// 获取POST数据
$input = file_get_contents('php://input');
$data = json_decode($input, true);
$userMessage = $data['user_message'] ?? '';

// 构造请求数据
$payload = [
    "model" => $MODEL_NAME,
    "messages" => [
        ["role" => "system", "content" => "你是一个智能助手"],
        ["role" => "user", "content" => $userMessage]
    ],
    "temperature" => 0.7
];

$headers = [
    'Content-Type: application/json',
    'Accept: application/json',
    'Authorization: Bearer ' . $API_KEY
];

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $API_URL);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

$response = curl_exec($ch);
$err = curl_error($ch);
curl_close($ch);

if ($err) {
    echo json_encode(['model_response' => '抱歉，暂时无法处理您的请求']);
} else {
    $responseData = json_decode($response, true);
    $answer = $responseData['choices'][0]['message']['content'] ?? '无法解析响应';
    echo json_encode(['model_response' => $answer]);
}
?>
    """

    # 写入文件
    with open("send_message.php", "w") as file:
        file.write(php_content)

    print("PHP file has been created successfully.")

if __name__ == "__main__":
    create_php_file()
