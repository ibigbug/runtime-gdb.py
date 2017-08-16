import gdb


class MemStatCmd(gdb.Command):
    """Show memory stats just like ReadMemStats"""

    def __init__(self):
        super(MemStatCmd, self).__init__("mstat", gdb.COMMAND_STACK, gdb.COMPLETE_NONE)

    @property
    def fmt_template(self):
        return '''\
runtime.MemStats
Alloc = {alloc}
TotalAlloc = {total_alloc}
Sys = {sys}
Lookups = {nlookup}
Mallocs = {nmalloc}
Frees = {nfree}
HeapAlloc = {heap_alloc}
HeapSys = {heap_sys}
HeapIdle = {heap_idle}
HeapInuse = {heap_inuse}
HeapReleased = {heap_released}
HeapObjects = {heap_objects}
Stack = {stacks_inuse} / {stacks_sys}
MSpan = {mspan_inuse} / {mspan_sys}
MCache = {mcache_inuse} / {mcache_sys}
BuckHashSys = {buckhash_sys}
GCSys = {gc_sys}
OtherSys = {other_sys}
NextGC = {next_gc}
LastGC = {last_gc}
NumGC = {numgc}
GCCPUFraction = {gc_cpu_fraction}
DebugGC = {debuggc}
'''

    def invoke(self, _arg, _from_tty):
        v = gdb.parse_and_eval("'runtime.memstats'")

        stats = {f.name: v[f.name] for f in v.type.fields()}
        # Stack numbers are part of the heap numbers, separate those out for user consumption
        stats['stacks_sys'] += stats['stacks_inuse']
        stats['heap_inuse'] -= stats['stacks_inuse']
        stats['heap_sys'] -= stats['stacks_inuse']

        gdb.write(self.fmt_template.format(**stats))
        gdb.flush()


class HeapdumpCmd(gdb.Command):
    """Do a heap dump"""

    def __init__(self):
        gdb.Command.__init__(self, "mdump", gdb.COMMAND_STACK, gdb.COMPLETE_NONE)
        self.mbuckets = None

    def invoke(self, _arg, _from_tty):
        self.mbuckets = gdb.parse_and_eval("'runtime.mbuckets'").dereference()
        n, ok = self.mem_profile()

        while True:
            # emm, it's golang style. anyway, translate first
            p = [None for i in range(n + 50)]
            n, ok = self.mem_profile(p, True)
            if ok:
                p = p[:n]
                break

        print(p)

    def mem_profile(self, p=None, inuse_zero=False):
        if p is None:
            p = []
        n = 0
        ok = False

        clear = True
        buckets = Bucket(self.mbuckets)
        for b in buckets:
            mp = b.mp()
            if inuse_zero or mp['alloc_bytes'] != mp['free_bytes']:
                n += 1
            if mp['allocs'] != 0 or mp['frees'] != 0:
                    clear = False

        if clear:
            mprof_GC()

        ok = True
        for idx, b in enumerate(buckets):
            mp = b.mp()
            if inuse_zero or mp['alloc_bytes'] != mp['free_bytes']:
                record(p, b, idx)

        return n, ok


class Bucket(object):
    def __init__(self, val):
        self.val = val

    def mp(self):
        b = self.val
        if b['typ'] != 1:
            raise ValueError("bad use of bucket.mp")

        data = add(
            b, b.type.sizeof + b['nstk'] * gdb.Value(0).type.sizeof
        )

        memRecord_t = gdb.lookup_type('struct runtime.memRecord')
        return data.cast(memRecord_t.pointer()).dereference()

    def stk(self):
        #TODO
        b = self.val
        stk = gdb.Value(add(b, b.type.sizeof))
        return stk.dereference()

    def __iter__(self):
        v = self.val

        while v:
            yield Bucket(v)
            v = v['allnext']
        raise StopIteration


def add(ptr, offset):
    return gdb.Value(ptr.address + offset)


def mprof_GC():
    """shouldn't happen when world stopped"""
    raise NotImplementedError('how do you turn this on')


def record(p, b, idx):
    mp = b.mp()
    d = {}
    d['alloc_bytes'] = mp['alloc_bytes']
    d['free_bytes'] = mp['free_bytes']
    d['alloc_objects'] = mp['allocs']
    d['free_objects'] = mp['frees']
    #TODO
    print(b.stk().type)


MemStatCmd()
HeapdumpCmd()
