/*
 * YARA Rule: Reverse Shell Detection
 * Detects reverse shell patterns across multiple languages
 */

rule Bash_Reverse_Shell {
    meta:
        description = "Detects bash reverse shell patterns"
        author = "Bionic Vuln Lab"
        severity = "critical"
        category = "reverse_shell"
    strings:
        $bash_dev_tcp = "/dev/tcp/" nocase
        $bash_dev_udp = "/dev/udp/" nocase
        $bash_sh_i = "sh -i" nocase
        $bash_bash_i = "bash -i" nocase
        $bash_exec = "exec " nocase
        $bash_0_1 = "0>&1" nocase
        $bash_1_0 = "1>&0" nocase
        $bash_2_1 = "2>&1" nocase
        $bash_pipe = "| bash" nocase
        $bash_socket = "socket.socket" nocase
    condition:
        ($bash_dev_tcp and $bash_sh_i) or
        ($bash_dev_tcp and $bash_bash_i) or
        ($bash_dev_udp and $bash_sh_i) or
        ($bash_exec and $bash_0_1) or
        ($bash_pipe and $bash_0_1) or
        ($bash_socket and $bash_0_1)
}

rule Python_Reverse_Shell {
    meta:
        description = "Detects Python reverse shell patterns"
        author = "Bionic Vuln Lab"
        severity = "critical"
        category = "reverse_shell"
    strings:
        $py_socket = "socket.socket(" nocase
        $py_subprocess = "subprocess.call(" nocase
        $py_os_dup2 = "os.dup2(" nocase
        $py_subprocess_popen = "subprocess.Popen(" nocase
        $py_pty = "pty.spawn(" nocase
        $py_connect = ".connect((" nocase
        $py_sh = "/bin/sh" nocase
        $py_bash = "/bin/bash" nocase
        $py_dev_tcp = "/dev/tcp/" nocase
    condition:
        ($py_socket and $py_connect and $py_os_dup2) or
        ($py_socket and $py_connect and $py_subprocess) or
        ($py_socket and $py_connect and $py_pty) or
        ($py_subprocess_popen and $py_sh) or
        ($py_subprocess_popen and $py_bash) or
        ($py_pty and $py_sh) or
        ($py_pty and $py_bash)
}

rule Perl_Reverse_Shell {
    meta:
        description = "Detects Perl reverse shell patterns"
        author = "Bionic Vuln Lab"
        severity = "critical"
        category = "reverse_shell"
    strings:
        $pl_socket = "Socket(" nocase
        $pl_connect = "connect(" nocase
        $pl_fileno = "fileno(" nocase
        $pl_dup2 = "dup2(" nocase
        $pl_exec = "exec " nocase
        $pl_system = "system(" nocase
        $pl_sh = "/bin/sh" nocase
        $pl_bash = "/bin/bash" nocase
        $pl_i = "-i" nocase
    condition:
        ($pl_socket and $pl_connect and $pl_dup2) or
        ($pl_socket and $pl_connect and $pl_exec) or
        ($pl_socket and $pl_connect and $pl_system) or
        ($pl_exec and $pl_sh and $pl_i) or
        ($pl_exec and $pl_bash and $pl_i)
}

rule Netcat_Reverse_Shell {
    meta:
        description = "Detects netcat reverse shell patterns"
        author = "Bionic Vuln Lab"
        severity = "critical"
        category = "reverse_shell"
    strings:
        $nc = "nc " nocase
        $nc_e = "nc -e" nocase
        $nc_l = "nc -l" nocase
        $nc_lvp = "nc -lvp" nocase
        $nc_ncat = "ncat " nocase
        $nc_ncat_e = "ncat -e" nocase
        $nc_sh = "nc /bin/sh" nocase
        $nc_bash = "nc /bin/bash" nocase
        $nc_pipe = "| nc " nocase
        $nc_backpipe = "nc |" nocase
    condition:
        $nc_e or $nc_lvp or $nc_ncat_e or
        ($nc and $nc_sh) or
        ($nc and $nc_bash) or
        $nc_pipe or $nc_backpipe
}

rule PHP_Reverse_Shell {
    meta:
        description = "Detects PHP reverse shell patterns"
        author = "Bionic Vuln Lab"
        severity = "critical"
        category = "reverse_shell"
    strings:
        $php_fsockopen = "fsockopen(" nocase
        $php_pfsockopen = "pfsockopen(" nocase
        $php_socket_create = "socket_create(" nocase
        $php_socket_connect = "socket_connect(" nocase
        $php_proc_open = "proc_open(" nocase
        $php_sh = "/bin/sh" nocase
        $php_bash = "/bin/bash" nocase
        $php_system = "system(" nocase
        $php_exec = "exec(" nocase
        $php_passthru = "passthru(" nocase
    condition:
        ($php_fsockopen and $php_sh) or
        ($php_fsockopen and $php_bash) or
        ($php_pfsockopen and $php_sh) or
        ($php_socket_create and $php_socket_connect) or
        ($php_proc_open and $php_sh) or
        ($php_proc_open and $php_bash)
}

rule PowerShell_Reverse_Shell {
    meta:
        description = "Detects PowerShell reverse shell patterns"
        author = "Bionic Vuln Lab"
        severity = "critical"
        category = "reverse_shell"
    strings:
        $ps_net_sockets = "Net.Sockets" nocase
        $ps_tcp_client = "TcpClient(" nocase
        $ps_get_stream = "GetStream(" nocase
        $ps_network_stream = "NetworkStream" nocase
        $ps_create_object = "CreateObject(" nocase
        $ps_wscript = "WScript.Shell" nocase
        $ps_run = ".Run(" nocase
        $ps_start_process = "Start-Process" nocase
        $ps_hidden = "-WindowStyle Hidden" nocase
    condition:
        ($ps_net_sockets and $ps_tcp_client and $ps_get_stream) or
        ($ps_network_stream and $ps_tcp_client) or
        ($ps_create_object and $ps_wscript and $ps_run) or
        ($ps_start_process and $ps_hidden)
}
