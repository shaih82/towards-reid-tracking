import DeepFried2 as df
from .. import dfext


def mknet():
    net = df.Sequential(
        # -> 128x48
        df.SpatialConvolutionCUDNN(3, 128, (7,7), border='same', bias=None),
        df.BatchNormalization(128, 0.95), df.ReLU(),

        dfext.resblock_bottle(128),
        df.PoolingCUDNN((2,2)),  # -> 64x24
        dfext.resblock_bottle(128),
        dfext.resblock_bottle(128),
        dfext.resblock_bottle(128, chan_out=256),
        df.PoolingCUDNN((2,2)),  # -> 32x12
        dfext.resblock_bottle(256),
        dfext.resblock_bottle(256),
        df.PoolingCUDNN((2,2)),  # -> 16x6
        dfext.resblock_bottle(256),
        dfext.resblock_bottle(256),
        dfext.resblock_bottle(256, chan_out=512),
        df.PoolingCUDNN((2,2)),  # -> 8x3
        dfext.resblock_bottle(512),
        dfext.resblock_bottle(512),
        df.PoolingCUDNN((8,3), mode='avg'),
        df.SpatialConvolutionCUDNN(512, 256, (1,1), bias=None),
        df.BatchNormalization(256, 0.95), df.ReLU(),
        df.StoreOut(df.SpatialConvolutionCUDNN(256, 128, (1,1))),
    )

    net.emb_mod = net[-1]
    net.in_shape = (128, 48)
    net.scale_factor = (2*2*2*2, 2*2*2*2)

    print("Net has {:.2f}M params".format(df.utils.count_params(net)/1000/1000), flush=True)
    return net


def hires_shared_twin(net):
    new_net = net[:]

    assert isinstance(new_net.modules[-5], df.PoolingCUDNN)
    new_net.modules[-5] = df.PoolingCUDNN((8,3), mode='average_exc_pad', stride=(1,1), padding=(4,1))

    return new_net


class Restrict(df.Module):
    def symb_forward(self, x):
        return x[:,:,1:,1:]


def ultrahires_shared_twin(net_hires):
    new_net = net_hires[:]

    assert isinstance(new_net.modules[-5], df.PoolingCUDNN)

    new_net.modules[4] = df.Sequential(df.PoolingCUDNN((2,2), stride=(1,1), padding=(1,1)), Restrict(), df.SpatialOverfeatRoll())
    new_net.modules[8] = df.Sequential(df.PoolingCUDNN((2,2), stride=(1,1), padding=(1,1)), Restrict(), df.SpatialOverfeatRoll())
    new_net.modules[11] = df.Sequential(df.PoolingCUDNN((2,2), stride=(1,1), padding=(1,1)), Restrict(), df.SpatialOverfeatRoll())
    new_net.modules[15] = df.Sequential(df.PoolingCUDNN((2,2), stride=(1,1), padding=(1,1)), Restrict(), df.SpatialOverfeatRoll())
    new_net.add(df.SpatialOverfeatUnroll())
    new_net.add(df.SpatialOverfeatUnroll())
    new_net.add(df.SpatialOverfeatUnroll())
    new_net.add(df.SpatialOverfeatUnroll())

    return new_net
