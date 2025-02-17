<?php
// 增强CORS支持
header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

// 启用错误报告（生产环境应关闭）
ini_set('display_errors', 1);
error_reporting(E_ALL);

// 从环境变量获取API密钥（更安全）
$API_KEY = getenv('DEEPSEEK_API_KEY') ?: 'sk-c65073ad363a493db1121bdddf1ef931';

// 日志记录函数
function log_debug($message) {
    file_put_contents('debug.log', date('[Y-m-d H:i:s] ') . $message . PHP_EOL, FILE_APPEND);
}

try {
    // 验证请求方法
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        throw new Exception('仅支持POST请求', 405);
    }

    // 获取并验证输入
    $input = json_decode(file_get_contents('php://input'), true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        throw new Exception('无效的JSON格式', 400);
    }
    
    $userMessage = trim($input['user_message'] ?? '');
    if (empty($userMessage)) {
        throw new Exception('问题内容不能为空', 400);
    }

    // 敏感词过滤示例
    $blacklist = ['恶意关键词1', '敏感信息2'];
    foreach ($blacklist as $word) {
        if (stripos($userMessage, $word) !== false) {
            throw new Exception('包含违禁内容', 403);
        }
    }

    // 构造API请求
    $payload = [
        "model" => "deepseek-chat",
        "messages" => [
            ["role" => "system", "content" => "你是一个智能助手"],
            ["role" => "user", "content" => $userMessage]
        ],
        "temperature" => 0.7,
        "max_tokens" => 1000
    ];

    $ch = curl_init();
    $options = [
        CURLOPT_URL => "https://api.deepseek.com/v1/chat/completions",
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            'Accept: application/json',
            'Authorization: Bearer ' . $API_KEY
        ],
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode($payload),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 15, // 15秒超时
        CURLOPT_SSL_VERIFYPEER => true // 生产环境必须验证SSL
    ];
    curl_setopt_array($ch, $options);

    // 执行请求
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);

    // 记录调试信息
    log_debug("请求内容: " . print_r($payload, true));
    log_debug("响应代码: $httpCode");
    log_debug("原始响应: " . $response);

    if ($error) {
        throw new Exception("cURL错误: $error", 500);
    }

    if ($httpCode >= 400) {
        throw new Exception("API请求失败 (HTTP $httpCode)", $httpCode);
    }

    $responseData = json_decode($response, true);
    if (!$responseData || !isset($responseData['choices'][0]['message']['content'])) {
        throw new Exception('API响应格式错误', 500);
    }

    // 返回成功响应
    echo json_encode([
        'status' => 'success',
        'model_response' => $responseData['choices'][0]['message']['content']
    ]);

} catch (Exception $e) {
    // 统一错误处理
    http_response_code($e->getCode() ?: 500);
    echo json_encode([
        'status' => 'error',
        'message' => $e->getMessage(),
        'code' => $e->getCode()
    ]);
    log_debug("错误: " . $e->getMessage());
}
?>