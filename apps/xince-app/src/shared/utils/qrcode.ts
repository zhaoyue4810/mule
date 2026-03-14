// @ts-expect-error vendor CJS module
import QRCodeCtor from "qrcode-terminal/vendor/QRCode";
// @ts-expect-error vendor CJS module
import QRErrorCorrectLevel from "qrcode-terminal/vendor/QRCode/QRErrorCorrectLevel";

export function createQrMatrix(content: string) {
  const qrCode = new QRCodeCtor(0, QRErrorCorrectLevel.M);
  qrCode.addData(content);
  qrCode.make();
  const size = qrCode.getModuleCount();
  const modules: boolean[][] = [];
  for (let row = 0; row < size; row += 1) {
    const rowModules: boolean[] = [];
    for (let col = 0; col < size; col += 1) {
      rowModules.push(Boolean(qrCode.isDark(row, col)));
    }
    modules.push(rowModules);
  }
  return {
    size,
    modules,
  };
}
