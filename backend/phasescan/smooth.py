import numpy as np

def shift_bpm_phases(xs, ys, step):
    smooth_start_idx = 0
    for i in range(xs.shape[0]):
        if abs((xs[i+1] - xs[i]) - step) < 0.1:
            smooth_start_idx = i
            break

    i = smooth_start_idx
    xs = np.roll(xs, -smooth_start_idx)
    ys = np.roll(ys, -smooth_start_idx)
    while i < xs.shape[0] - 1:
        shift_min, shift_max = -4, 4
        grads = []
        for j in range(shift_min, shift_max+1):
            grad = (ys[i+1]-ys[i]+j*360) / (xs[i+1]-xs[i])
            grads.append(grad)
        if i == smooth_start_idx:
            min_idx = np.argmin([abs(grad) for grad in grads])
        else:
            min_idx = np.argmin([abs(grad-prev_grad) for grad in grads])


        ys[i+1] += (shift_min + min_idx) * 360
        prev_grad = grads[min_idx]
        i += 1
    return np.roll(ys, smooth_start_idx)

def smooth_data(xs, ys, errs, step):
    xs, ys = rm_bad_point(xs, ys, errs)
    for i in range(ys.shape[1]):
        ys[:, i] = shift_bpm_phases(xs, ys[:, i], step)
    xs = np.ravel(xs)
    ys = np.transpose(ys)
    return {
        'xs': xs.tolist(),
        'ys': ys.tolist()
    }

def rm_bad_point(xs, ys, errs):
    xs, ys, errs = np.array(xs), np.asarray(ys), np.asarray(errs)
    xs = xs.reshape(-1, 1)
    ys = np.transpose(ys)
    errs = np.transpose(errs)
    avg_errs = np.average(errs, axis=0)
    reserved_limit = 3 * avg_errs
    reserved_idx = np.all(errs <= reserved_limit, axis=1)
    xs = xs[reserved_idx]
    ys = ys[reserved_idx]
    return xs, ys


