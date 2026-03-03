import time
import argparse
import pynvml

def get_dram_bandwidth_gbps(gpu_id=0, interval=1.0):
    pynvml.nvmlInit()
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)
        name = pynvml.nvmlDeviceGetName(handle)
        
        # Determine theoretical max memory bandwidth
        # Memory Clock in MHz, Bus Width in bits. 
        # Multiplied by 2 for Double Data Rate (DDR), divided by 8 for bytes, divided by 1000 for GB.
        mem_clock_mhz = pynvml.nvmlDeviceGetMaxClockInfo(handle, pynvml.NVML_CLOCK_MEM)
        bus_width_bits = pynvml.nvmlDeviceGetMemoryBusWidth(handle)
        max_bandwidth_gbps = (mem_clock_mhz * bus_width_bits * 2) / (8 * 1000.0)
        
        print(f"Monitoring GPU {gpu_id}: {name}")
        print(f"Theoretical Max Bandwidth: {max_bandwidth_gbps:.2f} GB/s")
        print("-" * 65)
        print(f"{'Time':<20} | {'DRAM Util %':<15} | {'Est. Throughput (GB/s)':<25}")
        print("-" * 65)

        total_util_pct = 0
        total_throughput_gbps = 0
        samples_count = 0

        while True:
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            mem_util = utilization.memory
            
            # The percentage memory utilization represents the time the memory controller was busy.
            # We estimate the GB/s throughput from the max bandwidth using this percentage.
            est_throughput = max_bandwidth_gbps * (mem_util / 100.0)
            
            print(f"{timestamp:<20} | {mem_util:<15} | {est_throughput:<25.2f}")
            
            total_util_pct += mem_util
            total_throughput_gbps += est_throughput
            samples_count += 1
            
            time.sleep(interval)
            
    except pynvml.NVMLError as e:
        print(f"NVML Error: {e}")
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
        if samples_count > 0:
            avg_util = total_util_pct / samples_count
            avg_throughput = total_throughput_gbps / samples_count
            print("-" * 65)
            print("Summary:")
            print(f"Total Samples    : {samples_count}")
            print(f"Avg DRAM Util %  : {avg_util:.2f} %")
            print(f"Avg Throughput   : {avg_throughput:.2f} GB/s")
            print("-" * 65)
    finally:
        pynvml.nvmlShutdown()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor GPU DRAM Bandwidth (Background Script)")
    parser.add_argument("--interval", type=float, default=1.0, help="Polling interval in seconds (default: 1.0)")
    parser.add_argument("--gpu_id", type=int, default=0, help="GPU ID to monitor (default: 0)")
    
    args = parser.parse_args()
    get_dram_bandwidth_gbps(args.gpu_id, args.interval)
