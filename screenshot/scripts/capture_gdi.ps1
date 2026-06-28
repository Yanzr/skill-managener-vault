$code = @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

public class ScreenCapture
{
    [DllImport("gdi32.dll")]
    static extern bool BitBlt(IntPtr hdc, int nXDest, int nYDest, int nWidth, int nHeight,
                              IntPtr hdcSrc, int nXSrc, int nYSrc, int dwRop);
    [DllImport("gdi32.dll")]
    static extern IntPtr CreateCompatibleDC(IntPtr hdc);
    [DllImport("gdi32.dll")]
    static extern IntPtr CreateCompatibleBitmap(IntPtr hdc, int nWidth, int nHeight);
    [DllImport("gdi32.dll")]
    static extern IntPtr SelectObject(IntPtr hdc, IntPtr hgdiobj);
    [DllImport("gdi32.dll")]
    static extern bool DeleteObject(IntPtr hObject);
    [DllImport("gdi32.dll")]
    static extern bool DeleteDC(IntPtr hdc);
    [DllImport("gdi32.dll")]
    static extern int GetDeviceCaps(IntPtr hdc, int nIndex);
    [DllImport("user32.dll")]
    static extern IntPtr GetDesktopWindow();
    [DllImport("user32.dll")]
    static extern IntPtr GetDC(IntPtr hWnd);
    [DllImport("user32.dll")]
    static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);
    [DllImport("user32.dll")]
    static extern bool EnumDisplaySettings(string lpszDeviceName, int iModeNum, ref DEVMODE lpDevMode);
    [DllImport("shcore.dll")]
    static extern int SetProcessDpiAwareness(int awareness);

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi)]
    struct DEVMODE
    {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
        public string dmDeviceName;
        public short dmSpecVersion;
        public short dmDriverVersion;
        public short dmSize;
        public short dmDriverExtra;
        public int dmFields;
        public int dmPositionX;
        public int dmPositionY;
        public int dmDisplayOrientation;
        public int dmDisplayFixedOutput;
        public short dmColor;
        public short dmDuplex;
        public short dmYResolution;
        public short dmTTOption;
        public short dmCollate;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
        public string dmFormName;
        public short dmLogPixels;
        public int dmBitsPerPel;
        public int dmPelsWidth;
        public int dmPelsHeight;
        public int dmDisplayFlags;
        public int dmDisplayFrequency;
        public int dmICMMethod;
        public int dmICMIntent;
        public int dmMediaType;
        public int dmDitherType;
        public int dmReserved1;
        public int dmReserved2;
        public int dmPanningWidth;
        public int dmPanningHeight;
    }

    const int SRCCOPY   = 0x00CC0020;
    const int HORZRES   = 8;
    const int VERTRES   = 10;
    const int PROCESS_SYSTEM_DPI_AWARE = 1;

    public static void Capture(string filePath)
    {
        try { SetProcessDpiAwareness(PROCESS_SYSTEM_DPI_AWARE); } catch {}

        int width = 0, height = 0;

        DEVMODE dm = new DEVMODE();
        dm.dmSize = (short)Marshal.SizeOf(typeof(DEVMODE));
        if (EnumDisplaySettings(null, -1, ref dm))
        {
            width  = dm.dmPelsWidth;
            height = dm.dmPelsHeight;
        }

        if (width <= 0 || height <= 0)
        {
            IntPtr dw = GetDesktopWindow();
            IntPtr dc = GetDC(dw);
            width  = GetDeviceCaps(dc, HORZRES);
            height = GetDeviceCaps(dc, VERTRES);
            ReleaseDC(dw, dc);
        }

        if (width <= 0) width  = 1920;
        if (height <= 0) height = 1080;

        IntPtr desktopWnd = GetDesktopWindow();
        IntPtr screenDC   = GetDC(desktopWnd);
        IntPtr memDC      = CreateCompatibleDC(screenDC);
        IntPtr bmp        = CreateCompatibleBitmap(screenDC, width, height);
        IntPtr oldBmp     = SelectObject(memDC, bmp);

        BitBlt(memDC, 0, 0, width, height, screenDC, 0, 0, SRCCOPY);

        SelectObject(memDC, oldBmp);

        using (var image = Image.FromHbitmap(bmp))
        {
            image.Save(filePath, ImageFormat.Png);
        }

        DeleteObject(bmp);
        DeleteDC(memDC);
        ReleaseDC(desktopWnd, screenDC);
    }
}
'@

Add-Type -TypeDefinition $code -ReferencedAssemblies "System.Drawing"

$output = if ($args.Count -gt 0) { $args[0] } else { "$HOME\Desktop\screenshot.png" }
[ScreenCapture]::Capture($output)
Write-Output "Screenshot saved: $output"
