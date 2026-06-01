import asyncio
import os
import time

import pytest

from pyxxl import ExecutorConfig
from pyxxl.enum import executorBlockStrategy
from pyxxl.executor import Executor, JobHandler
from pyxxl.schema import RunData
from pyxxl.tests.utils import MokeXXL


@pytest.fixture(scope="module")
def process_pool_config() -> ExecutorConfig:
    return ExecutorConfig(
        xxl_admin_baseurl="http://localhost:8080/xxl-job-admin/api/",
        executor_app_name="test-process-pool",
        executor_listen_host="127.0.0.1",
        executor_pool_type="process",
        max_workers=2,
        task_queue_length=5,
        dotenv_try=False,
    )


@pytest.fixture(scope="module")
def process_executor(process_pool_config: ExecutorConfig) -> Executor:
    return Executor(
        MokeXXL("http://localhost:8080/xxl-job-admin/api/"),
        process_pool_config,
        handler=None,
    )


process_job_handler = JobHandler(use_process=True)


@process_job_handler.register
def pytest_process_task():
    pid = os.getpid()
    time.sleep(1)
    return f"process task done, pid={pid}"


@process_job_handler.register
def pytest_process_cpu_task():
    pid = os.getpid()
    result = sum(i * i for i in range(100000))
    return f"cpu task done, pid={pid}, result={result}"


@pytest.mark.asyncio
async def test_process_pool_creation(process_executor: Executor):
    from concurrent.futures import ProcessPoolExecutor

    assert isinstance(process_executor.pool, ProcessPoolExecutor)
    assert process_executor.config.executor_pool_type == "process"
    assert process_executor.handler.use_process is True


@pytest.mark.asyncio
async def test_process_pool_basic_execution(process_executor: Executor):
    process_executor.reset_handler(process_job_handler)
    process_executor.xxl_client.clear_result()

    data = RunData.from_dict(
        dict(
            logId=100,
            jobId=100,
            executorHandler="pytest_process_task",
            executorBlockStrategy=executorBlockStrategy.SERIAL_EXECUTION.value,
        )
    )
    await process_executor.run_job(data)
    await process_executor.graceful_close()

    assert process_executor.xxl_client.callback_result.get(100) == 200


@pytest.mark.asyncio
async def test_process_pool_concurrent_execution(process_executor: Executor):
    process_executor.reset_handler(process_job_handler)
    process_executor.xxl_client.clear_result()

    tasks = []
    for i in range(3):
        data = RunData.from_dict(
            dict(
                logId=200 + i,
                jobId=200 + i,
                executorHandler="pytest_process_task",
                executorBlockStrategy=executorBlockStrategy.SERIAL_EXECUTION.value,
            )
        )
        tasks.append(process_executor.run_job(data))

    await asyncio.gather(*tasks)
    await process_executor.graceful_close()

    for i in range(3):
        assert process_executor.xxl_client.callback_result.get(200 + i) == 200


@pytest.mark.asyncio
async def test_process_pool_cpu_intensive(process_executor: Executor):
    process_executor.reset_handler(process_job_handler)
    process_executor.xxl_client.clear_result()

    data = RunData.from_dict(
        dict(
            logId=300,
            jobId=300,
            executorHandler="pytest_process_cpu_task",
            executorBlockStrategy=executorBlockStrategy.SERIAL_EXECUTION.value,
        )
    )
    await process_executor.run_job(data)
    await process_executor.graceful_close()

    assert process_executor.xxl_client.callback_result.get(300) == 200


@pytest.mark.asyncio
async def test_process_pool_serial_execution(process_executor: Executor):
    process_executor.reset_handler(process_job_handler)
    process_executor.xxl_client.clear_result()

    job_id = 400
    run_data = dict(
        jobId=job_id,
        executorHandler="pytest_process_task",
        executorBlockStrategy=executorBlockStrategy.SERIAL_EXECUTION.value,
    )

    await process_executor.run_job(RunData(logId=401, **run_data))
    await process_executor.run_job(RunData(logId=402, **run_data))
    await process_executor.run_job(RunData(logId=403, **run_data))

    assert process_executor.queue.get(job_id).qsize() == 2

    await process_executor.graceful_close()

    assert process_executor.queue.get(job_id).qsize() == 0
    assert process_executor.xxl_client.callback_result.get(403) == 200


@pytest.mark.asyncio
async def test_process_pool_discard_later(process_executor: Executor):
    from pyxxl.error import JobDuplicateError

    process_executor.reset_handler(process_job_handler)
    process_executor.xxl_client.clear_result()

    job_id = 500
    run_data = dict(
        jobId=job_id,
        executorHandler="pytest_process_task",
        executorBlockStrategy=executorBlockStrategy.DISCARD_LATER.value,
    )

    await process_executor.run_job(RunData(logId=501, **run_data))

    with pytest.raises(JobDuplicateError):
        await process_executor.run_job(RunData(logId=502, **run_data))

    await process_executor.graceful_close()

    assert process_executor.xxl_client.callback_result.get(501) == 200
    assert process_executor.xxl_client.callback_result.get(502) is None


@pytest.mark.asyncio
async def test_process_pool_not_blocking_event_loop(process_executor: Executor):
    process_executor.reset_handler(process_job_handler)
    process_executor.xxl_client.clear_result()

    start_time = time.time()
    heartbeat_count = 0

    async def mock_heartbeat():
        nonlocal heartbeat_count
        while True:
            heartbeat_count += 1
            await asyncio.sleep(0.5)

    heartbeat_task = asyncio.create_task(mock_heartbeat())

    data = RunData.from_dict(
        dict(
            logId=600,
            jobId=600,
            executorHandler="pytest_process_task",
            executorBlockStrategy=executorBlockStrategy.SERIAL_EXECUTION.value,
        )
    )
    await process_executor.run_job(data)
    await process_executor.graceful_close()

    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass

    elapsed = time.time() - start_time
    assert heartbeat_count >= 1
    assert elapsed >= 1.0
