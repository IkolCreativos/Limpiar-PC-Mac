import Foundation
import CoreGraphics

// Cuenta paginas de un PDF (o .ai con compatibilidad PDF) de forma fiable,
// via CoreGraphics. Contar la cadena "/Type/Page" en el binario NO sirve:
// Ghostscript reescribe la estructura y comprime los objetos, asi que el
// recuento cambia sin que cambien las paginas.
// Compilar:  swiftc -O -o pdfpaginas pdfpaginas.swift
// Imprime el numero de paginas, o -1 si no se puede abrir.
let a = CommandLine.arguments
guard a.count == 2, let doc = CGPDFDocument(URL(fileURLWithPath: a[1]) as CFURL) else {
    print(-1); exit(1)
}
print(doc.numberOfPages)
