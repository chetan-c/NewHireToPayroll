
from integration.workday_client import WorkdayClient


def main():
    client = WorkdayClient(access_token="local-test-token")

    print("Connecting to Mock Workday API...")

    workers = client.get_all_workers(page_size=2)

    print("\nWorkers retrieved successfully:")
    print("--------------------------------")

    for worker in workers:
        print(
            worker["employeeId"],
            worker["firstName"],
            worker["lastName"],
            worker["department"]
        )

    print("--------------------------------")
    print("Total workers retrieved:", len(workers))


if __name__ == "__main__":
    main()
