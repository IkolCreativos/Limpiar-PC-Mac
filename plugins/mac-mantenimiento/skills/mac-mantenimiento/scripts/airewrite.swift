import Foundation
import CoreGraphics

let a = CommandLine.arguments
guard a.count == 3 else { FileHandle.standardError.write("uso: airewrite ENTRADA SALIDA\n".data(using:.utf8)!); exit(2) }
let inURL = URL(fileURLWithPath: a[1]), outURL = URL(fileURLWithPath: a[2])
guard let doc = CGPDFDocument(inURL as CFURL), doc.numberOfPages > 0 else {
    FileHandle.standardError.write("no se pudo abrir como PDF\n".data(using:.utf8)!); exit(1)
}
guard let first = doc.page(at: 1) else { exit(1) }
var box = first.getBoxRect(.mediaBox)
guard let ctx = CGContext(outURL as CFURL, mediaBox: &box, nil) else {
    FileHandle.standardError.write("no se pudo crear el PDF de salida\n".data(using:.utf8)!); exit(1)
}
for i in 1...doc.numberOfPages {
    guard let pg = doc.page(at: i) else { continue }
    var r = pg.getBoxRect(.mediaBox)
    ctx.beginPage(mediaBox: &r); ctx.drawPDFPage(pg); ctx.endPage()
}
ctx.closePDF()
// reabrir la salida y confirmar paginas y dimensiones
guard let out = CGPDFDocument(outURL as CFURL), let p1 = out.page(at: 1) else {
    FileHandle.standardError.write("la salida no se puede reabrir\n".data(using:.utf8)!); exit(1)
}
let b1 = first.getBoxRect(.mediaBox), b2 = p1.getBoxRect(.mediaBox)
print("in=\(doc.numberOfPages) out=\(out.numberOfPages) w=\(Int(b1.width))/\(Int(b2.width)) h=\(Int(b1.height))/\(Int(b2.height))")

// Compilar:  swiftc -O -o airewrite airewrite.swift
//
// Reescribe un PDF o un .ai con compatibilidad PDF conservando los VECTORES y
// soltando los datos privados de la aplicacion de origen (AIPrivateData).
// Imprime "in=N out=M w=../.. h=../.." para verificar que nada se perdio.
//
// NO recomprime las imagenes incrustadas: si el peso del archivo son fotos
// dentro, esto no gana nada y hay que usar reducir_incrustadas.py (ghostscript).
//
// AVISO: si el .ai se guardo SIN compatibilidad PDF, su capa PDF esta vacia y
// esta herramienta lo deja en blanco. Comprobar SIEMPRE que el original
// renderiza con contenido antes de reescribirlo (lo hace aplanar_ilustracion.py).
