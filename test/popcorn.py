import random
import sys
import time


def main():
    kernel_num = 25
    kernels = "." * kernel_num
    sys.stdout.write(str(kernels))
    kernel_count = []
    for k in range(0, kernel_num):
        kernel_count.append(k)
    for k in range(0, kernel_num):
        time.sleep(random.choice([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]))
        sys.stdout.write("\r")
        pop = random.choice(kernel_count)
        kernel_count.remove(pop)
        kernels = list(kernels)
        kernels[pop] = random.choice(["o", "Q", "0", "O"])
        kernels = "".join(kernels)
        sys.stdout.write(str(kernels))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
