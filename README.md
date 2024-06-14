## API
GET /task タスクの一覧を取得 <br> POST /task タスクを追加 <br> PUT /task/{task_id}　タスクを完了 <br> DELETE /task/{task_id}  タスクを消去<br>

![Task Management API Architecture](task_aws.png)


## 使用技術
- APIGateway
- Lambda
- DynamoDB
- s3