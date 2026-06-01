import logging
import time

from pyxxl import ExecutorConfig, PyxxlRunner

logger = logging.getLogger(__name__)

# 进程池模式配置示例
# 适用于长时间运行的同步任务（如2-3小时），不会阻塞事件循环
config = ExecutorConfig(
    xxl_admin_baseurl="http://localhost:8080/xxl-job-admin/api/",
    executor_app_name="xxl-job-executor-sample",
    executor_listen_host="127.0.0.1",
    executor_pool_type="process",  # 使用进程池模式
    max_workers=4,  # 进程池大小，建议设置为CPU核心数
    debug=True,
)

app = PyxxlRunner(config)


@app.register(name="process_long_task")
def long_running_task():
    """
    长时间运行的同步任务示例
    在进程池模式下，此任务会在独立进程中执行，不会阻塞事件循环
    """
    logger.info("开始执行长时间任务，PID: %s", __import__("os").getpid())

    # 模拟长时间运行的任务
    for i in range(10):
        logger.info("任务进度: %d/10", i + 1)
        time.sleep(2)

    logger.info("长时间任务执行完成")
    return "长时间任务成功完成"


@app.register(name="process_cpu_task")
def cpu_intensive_task():
    """
    CPU密集型任务示例
    在进程池模式下，可以充分利用多核CPU进行并行计算
    """
    logger.info("开始CPU密集型任务，PID: %s", __import__("os").getpid())

    # 模拟CPU密集型计算
    result = 0
    for i in range(10000000):
        result += i * i

    logger.info("CPU密集型任务完成，结果: %d", result)
    return f"计算结果: {result}"


@app.register(name="process_file_task")
def file_processing_task():
    """
    文件处理任务示例
    在进程池模式下，文件IO操作不会阻塞主进程
    """
    import os
    import tempfile

    logger.info("开始文件处理任务，PID: %s", os.getpid())

    # 创建临时文件并写入数据
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for i in range(100):
            f.write(f"Line {i}: Process pool example data\n")
        temp_path = f.name

    # 读取并处理文件
    with open(temp_path, "r") as f:
        lines = f.readlines()

    # 清理临时文件
    os.unlink(temp_path)

    logger.info("文件处理任务完成，处理了 %d 行", len(lines))
    return f"处理了 {len(lines)} 行数据"


if __name__ == "__main__":
    app.run_executor()
