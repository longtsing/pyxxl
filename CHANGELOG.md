### 0.4.2
* 新增配置 **executor_pool_type**, 支持进程池模式执行同步任务
  - 可选值: "thread"（线程池，默认）、"process"（进程池）
  - 进程池模式下同步任务不会阻塞事件循环，解决长时间运行任务导致执行器离线的问题
  - 支持多核CPU并行计算，进程间隔离
* 新增进程池模式示例文件 `example/process_pool_app.py`
* 新增进程池模式单元测试 `tests/test_process_pool.py`
* 优化 `get_network_ip()` 函数，支持macOS系统获取真实IP地址
* 优化 `DiskLog.get_logs()` 方法，使用异步迭代器提高性能
* 优化日志格式，添加进程ID显示，便于进程池模式调试
* 优化 `RedisLog.read_task_logs()` 方法，使用 `asyncio.to_thread` 避免阻塞事件循环
* 修复 `prometheus.py` 中的 `thread_pool` 引用，支持进程池模式监控

### 0.4.1
* 修复配置中host和port的优先级 #68

### 0.4.0
* 配置移除 **executor_host** **executor_port** 使用 **executor_url** 替代
* 配置新增 **executor_logger**, 用于传入自定义logger[目前只能覆盖executor的日志]

### 0.3.4
* **executor_server_host** 修改为 **executor_listen_host**
* 新增配置 **executor_listen_port**

### 0.3.3
* 兼容XXL-JOB 2.2版本

### 0.1.7

* 优化错误信息
* 支持自定义执行器参数
* 支持executorTimeout
