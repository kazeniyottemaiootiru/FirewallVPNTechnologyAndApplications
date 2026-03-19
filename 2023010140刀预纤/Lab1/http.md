# Lab1：又见面了， HTTP/HTTPS！

## 实验背景

HTTP（HyperText Transfer Protocol，超文本传输协议）是应用层最核心的协议之一。每次打开网页，浏览器与服务器之间就在用 HTTP"对话"。

一次典型的 HTTP 交互分为两部分：

```
浏览器 ──── HTTP 请求 ────▶ 服务器
浏览器 ◀─── HTTP 响应 ──── 服务器
```

**请求报文**结构示例：

```http
GET /index.html HTTP/1.1
Host: www.example.com
User-Agent: Mozilla/5.0
Accept: text/html
```

**响应报文**结构示例：

```http
HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 1234

<html>...</html>
```

HTTPS 在 HTTP 基础上加入了 TLS 加密，报文内容在传输过程中无法被直接读取。但**浏览器开发者工具**运行在加密之前，可以看到完整的明文请求和响应，是分析 HTTP/HTTPS 协议最方便的入门工具。

---

## 实验任务

1. 用 Chrome 或 Edge 浏览器访问任意 **HTTPS** 站点，例如 `https://www.yxnu.edu.cn/`。
2. 按 `F12`（macOS 用 `Command + Option + I`）打开**开发者工具**，切换到 **Network（网络）** 面板。
3. 刷新页面，等待请求列表加载完成。
4. 点击列表中第一条请求（通常是页面本身），在右侧查看 **Headers** 标签页，找到 Request Headers 和 Response Headers。
5. 对请求头区域和响应头区域分别**截图**，并按规范命名（见下方截图要求）。
6. 根据截图，完成下方的知识填空。

> **提示**：开发者工具打开路径：浏览器右上角菜单 → 更多工具 → 开发者工具，或直接右键页面空白处 → 检查。

---

## 截图要求

- 截图须清晰显示开发者工具 Network 面板中的 **Headers** 区域，能看到具体字段名和值。
- 截图文件与本 `http.md` 放在**同一目录**下。
- 命名规范：

| 截图内容                       | 文件名                                 |
| :----------------------------- | :------------------------------------- |
| Request Headers（请求头）截图  |  `req.png`  ( jpg或 jpeg 格式也可以)   |
| Response Headers（响应头）截图 | `resp.png`  ( jpg或 jpeg 格式也可以)   |

截图示例位置（填写时直接在下方嵌入）：

```markdown
![请求头截图](req.png)
![响应头截图](resp.png)
```

---

## 知识填空

> 根据你的截图，填写以下空白处。不确定的字段请写"截图中未见"，**不得留空不填**。

### A. 请求头（Request Headers）

| 字段               | 你的截图中的值 |
| :----------------- | :------------- |
| 请求方法（Method） |  GET           |
| 请求路径（URI）    |  /images/shenruxuexiguanchedangdeershijiesizhongquanhuijingshen.jpg
| 协议版本           |  HTTP/1.1      |
| Host               |  www.yxnu.edu.cn             |
| User-Agent         |  Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36 Edg/146.0.0.0              |

**嵌入截图：**

![请求头截图](req.png)

---

### B. 响应头（Response Headers）

| 字段                  | 你的截图中的值 |
| :-------------------- | :------------- |
| 状态码（Status Code） |   200     |
| 状态描述              |   ok      |
| Content-Type          |  image/jpeg    |
| Server（若可见）      |     none       |

**嵌入截图：**

![响应头截图](resp.png)

---

### C. 知识问答

1. HTTP 请求报文由哪几部分构成？请按顺序列出：

   > 答：
请求行：包含请求方法、请求 URI、协议版本
请求头：包含客户端环境、请求资源属性等键值对信息
空行：分隔请求头与请求体，标识请求头结束
请求体（可选）：携带 POST 等方法提交的数据

2. 状态码 `404` 代表什么含义？状态码 `500` 和 `503` 有什么区别？

   > 答：
   404：代表资源未找到，服务器无法找到客户端请求的资源。
   500：服务器内部错误，服务器在处理请求时发生了意外情况。
   503：服务不可用，服务器暂时无法处理请求（通常是过载、维护或资源不足导致）。
区别：500 是服务器本身处理逻辑出错，503 是服务器暂时无法提供服务（并非逻辑错误）。

3. GET 与 POST 方法的主要区别是什么？各适用于什么场景？

   > 答：
   主要区别
参数位置：GET 参数在 URL 后（可见、长度受限）；POST 参数在请求体中（不可见、长度不限）。
安全性：GET 易被缓存、留痕，安全性低；POST 不易留痕，安全性更高。
数据类型：GET 仅支持 ASCII；POST 支持文本、二进制等多种类型。
幂等性：GET 无副作用、幂等；POST 有副作用、非幂等。
适用场景
GET：获取 / 查询资源（如浏览页面、搜索）。
POST：提交 / 修改数据（如登录、上传文件、表单提交）。

4. HTTP 与 HTTPS 有什么区别？HTTPS 使用了什么机制来保护数据？

   > 答：
   区别：
HTTP 是明文传输，数据易被窃听、篡改；HTTPS 是加密传输，数据更安全。
HTTP 默认端口 80，HTTPS 默认端口 443。
HTTPS 需要 CA 证书验证服务器身份，HTTP 无身份验证。
保护机制：
HTTPS 基于 TLS/SSL 协议，通过对称加密保护传输数据，非对称加密交换对称密钥，数字证书验证服务器身份，消息摘要防止数据被篡改。

5. 既然 HTTPS 已经加密，为什么浏览器开发者工具仍然能看到请求和响应的明文内容？

   > 答：HTTPS 加密是客户端与服务器之间的端到端加密，浏览器作为通信的一端，在收到加密数据后会先解密还原为明文，再渲染页面。开发者工具是浏览器内置的调试工具，运行在浏览器进程中，因此可以直接访问解密后的明文请求与响应内容，并非绕过了 HTTPS 加密。

---

## 提交要求

在自己的文件夹下新建 `Lab1/` 目录，提交以下文件：

```
学号姓名/
└── Lab1/
    ├── http.md     # 本文件（填写完整）
    ├── req.png       # HTTP 请求截图 (除 png 外，使用 jpg 或者 jpeg 格式也可以)
    └── resp.png      # HTTP 响应截图 (除 png 外，使用 jpg 或者 jpeg 格式也可以) 
```

---

## 截止时间

2026-3-26，届时关于 Lab1 的 PR 请求将不会被合并。

---

## 参考资料

- [HTTP - MDN Web Docs](https://developer.mozilla.org/zh-CN/docs/Web/HTTP)
- [HTTP 状态码列表 - MDN](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status)

