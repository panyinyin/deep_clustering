from contextlib import contextmanager
import time
import torch
import shutil
import os


def save_checkpoint(state, is_best, filepath='checkpoint.pth.tar', best_suffix=''):
    torch.save(state, filepath)
    if is_best:
        shutil.copyfile(filepath,
                        os.path.join(os.path.dirname(filepath), 'model_best{}.pth.tar'.format(best_suffix)))


class AverageMeter(object):
    """Computes and stores the average and current value"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count


def accuracy(output, target, topk=(1,)):
    """Computes the precision@k for the specified values of k"""
    with torch.no_grad():
        maxk = max(topk)
        batch_size = target.size(0)

        _, pred = output.topk(maxk, 1, True, True)
        pred = pred.t()
        correct = pred.eq(target.view(1, -1).expand_as(pred))

        res = []
        for k in topk:
            correct_k = correct[:k].view(-1).float().sum(0, keepdim=True)
            res.append(correct_k.mul_(100.0 / batch_size))
        return res


class CyclicLr(object):
    def __init__(self, start_epoch, init_lr=1e-2, num_epochs_per_cycle=12, epochs_pro_decay=2,
                 lr_decay_factor=0.5):
        self.start_epoch = start_epoch
        self.init_lr = init_lr
        self.lr_decay_factor = lr_decay_factor
        self.num_epochs_per_cycle = num_epochs_per_cycle
        self.epochs_pro_decay = epochs_pro_decay

    def __call__(self, epoch):
        cur_epoch_in_cycle = (epoch - self.start_epoch) % self.num_epochs_per_cycle
        lr = self.init_lr * (self.lr_decay_factor ** int(cur_epoch_in_cycle / self.epochs_pro_decay))
        return lr


class StepMinLr(object):
    def __init__(self, start_epoch, init_lr=1e-2, epochs_pro_decay=2,
                 lr_decay_factor=0.5, min_lr=None):
        self.start_epoch = start_epoch
        self.init_lr = init_lr
        self.lr_decay_factor = lr_decay_factor
        self.epochs_pro_decay = epochs_pro_decay
        self.min_lr = min_lr

    def __call__(self, epoch):
        cur_epoch = epoch - self.start_epoch
        lr = self.init_lr * (self.lr_decay_factor ** int(cur_epoch / self.epochs_pro_decay))
        if self.min_lr is not None:
            lr = max(lr, self.min_lr)
        return lr


@contextmanager
def timed_operation(msg, log_start=False, tformat='s'):
    """
    Surround a context with a timer.

    Args:
        msg(str): the log to print.
        log_start(bool): whether to print also at the beginning.
        format: one of {s, m, h} - seconds, minutes or hours
    Example:
        .. code-block:: python

            with timed_operation('Good Stuff'):
                time.sleep(1)

        Will print:

        .. code-block:: python

            Good stuff finished, time:1sec.
    """
    if log_start:
        print('Start {} ...'.format(msg))
    start = time.time()
    yield
    if tformat == 's':
        ns = 1.
    if tformat == 'm':
        ns = 60.
    elif tformat == 'h':
        ns = 60.0**2
    elif tformat == 'd':
        ns = 60.0**2 * 24.0
    else:
        raise ValueError('Unknown tformat={}'.format(tformat))
    print('{} finished, time:{:.4f}{}.'.format(
        msg, (time.time() - start) / ns, tformat))
