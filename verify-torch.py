import torch


# https://pytorch.org/get-started/locally/#mac-verification
def offical_verify():
    x = torch.rand(5, 3)
    print(x)


# https://developer.apple.com/metal/pytorch/
def mac_m_verify():
    if torch.backends.mps.is_available():
        mps_device = torch.device("mps")
        x = torch.ones(1, device=mps_device)
        print(x)
    else:
        print("MPS device not found.")


if __name__ == "__main__":
    offical_verify()
    mac_m_verify()
