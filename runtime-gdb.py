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
        v = gdb.parse_and_eval("'runtime.mbuckets'")
        self.mbuckets = v.dereference()

    def mem_profile(self, p=None, inuse_zero=False):
        clear = True

        current = self.mbuckets
        while current is not None:
            pass


MemStatCmd()
HeapdumpCmd()
