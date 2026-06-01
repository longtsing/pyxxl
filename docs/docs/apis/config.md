# ExecutorConfig

::: pyxxl.ExecutorConfig

## 新增配置项

### executor_pool_type

执行器池类型，用于控制同步任务的执行方式。

**类型**: `Literal["thread", "process"]`  
**默认值**: `"thread"`

#### 可选值

| 值 | 说明 |
|---|------|
| `"thread"` | 使用线程池执行同步任务（默认） |
| `"process"` | 使用进程池执行同步任务 |

#### 使用示例

```python
from pyxxl import ExecutorConfig, PyxxlRunner

# 使用进程池模式
config = ExecutorConfig(
    xxl_admin_baseurl="http://localhost:8080/xxl-job-admin/api/",
    executor_app_name="xxl-job-executor-sample",
    executor_pool_type="process",  # 关键配置
    max_workers=10,  # 进程池大小，建议设置为CPU核心数
)

app = PyxxlRunner(config)

@app.register(name="my_task")
def my_task():
    # 同步任务会在独立进程中执行，不会阻塞事件循环
    import time
    time.sleep(3600)
    return "完成"
```

#### 线程池 vs 进程池 对比

| 特性 | 线程池 (thread) | 进程池 (process) |
|------|----------------|-----------------|
| 事件循环阻塞 | 会阻塞 | **不会阻塞** |
| CPU 利用率 | 受 GIL 限制 | **可利用多核** |
| 内存隔离 | 共享内存 | **进程隔离** |
| 心跳任务 | 可能受影响 | **正常运行** |
| 任务函数限制 | 无特殊限制 | 必须可序列化 |
| 全局状态 | 可共享 | 不可共享 |

#### 注意事项

!!! warning "进程池模式注意事项"

    1. **任务函数必须是可序列化的**：不能使用 lambda、闭包等
    2. **不能使用共享的全局状态**：进程间内存隔离
    3. **不能使用 `g.logger`**：上下文变量在进程间不共享，需要使用普通 logger
    4. **进程间通信开销较大**：适合长时间运行的任务

#### 适用场景

- **线程池模式**：任务较短、IO 密集型、需要共享全局状态
- **进程池模式**：任务较长（如 2-3 小时）、CPU 密集型、需要避免阻塞事件循环
