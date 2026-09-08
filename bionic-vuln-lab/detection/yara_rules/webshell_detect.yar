/*
 * YARA Rule: PHP/ASP/JSP Webshell Detection
 * Detects common webshell patterns and backdoors
 */

rule PHP_Webshell_Generic {
    meta:
        description = "Detects generic PHP webshells"
        author = "Bionic Vuln Lab"
        severity = "high"
        category = "webshell"
    strings:
        $php_tag = "<?php"
        $eval = "eval(" nocase
        $exec = "exec(" nocase
        $system = "system(" nocase
        $passthru = "passthru(" nocase
        $shell_exec = "shell_exec(" nocase
        $assert = "assert(" nocase
        $base64_decode = "base64_decode(" nocase
        $gzinflate = "gzinflate(" nocase
        $str_rot13 = "str_rot13(" nocase
        $preg_replace_e = /preg_replace\s*\(.*\/e/
        $cmd_pattern = /\$_GET\s*\[\s*['"]cmd['"]\s*\]/
    condition:
        $php_tag and (
            ($eval and $base64_decode) or
            ($eval and $gzinflate) or
            ($system and $cmd_pattern) or
            ($passthru and $cmd_pattern) or
            ($shell_exec and $cmd_pattern) or
            ($preg_replace_e) or
            ($assert and $base64_decode) or
            ($str_rot13 and $base64_decode)
        )
}

rule ASP_Webshell_Generic {
    meta:
        description = "Detects generic ASP/ASPX webshells"
        author = "Bionic Vuln Lab"
        severity = "high"
        category = "webshell"
    strings:
        $asp_tag = "<%@"
        $execute = "Execute(" nocase
        $eval = "Eval(" nocase
        $create_object = "CreateObject(" nocase
        $wscript = "WScript.Shell" nocase
        $adodb = "ADODB.Stream" nocase
        $scripting = "Scripting.FileSystemObject" nocase
        $shell_app = "Shell.Application" nocase
    condition:
        $asp_tag and (
            ($execute and $create_object) or
            ($eval and $wscript) or
            ($create_object and $adodb) or
            ($create_object and $scripting) or
            ($create_object and $shell_app)
        )
}

rule JSP_Webshell_Generic {
    meta:
        description = "Detects generic JSP webshells"
        author = "Bionic Vuln Lab"
        severity = "high"
        category = "webshell"
    strings:
        $jsp_tag = "<%@ page"
        $runtime = "Runtime.getRuntime()" nocase
        $process_builder = "ProcessBuilder(" nocase
        $exec_method = ".exec(" nocase
        $input_stream = "getInputStream()" nocase
        $output_stream = "getOutputStream()" nocase
        $class_forName = "Class.forName(" nocase
        $define_class = "defineClass(" nocase
        $url_classloader = "URLClassLoader(" nocase
    condition:
        $jsp_tag and (
            ($runtime and $exec_method) or
            ($process_builder and $exec_method) or
            ($class_forName and $define_class) or
            ($url_classloader and $define_class)
        )
}

rule Generic_Webshell_Indicators {
    meta:
        description = "Detects common webshell indicators across languages"
        author = "Bionic Vuln Lab"
        severity = "medium"
        category = "webshell"
    strings:
        $c99 = "c99shell" nocase
        $r57 = "r57shell" nocase
        $wso = "wso" nocase
        $b374k = "b374k" nocase
        $cih = "cihshell" nocase
        $h4x0r = "h4x0r" nocase
        $adminer = "adminer" nocase
        $password_field = "type=\"password\"" nocase
        $upload_form = "multipart/form-data" nocase
    condition:
        any of ($c99, $r57, $wso, $b374k, $cih, $h4x0r) or
        ($adminer and $password_field) or
        ($upload_form and $password_field)
}
