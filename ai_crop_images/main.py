from time import sleep
import datetime
import argparse
from pathlib import Path
from progressbar import progressbar
from ai_crop_images.image_scanner import im_scan
import sys

if sys.version_info >= (3, 8):
    from importlib.metadata import version
else:
    from importlib_metadata import version
from rich import print


def exception_keyboard(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except KeyboardInterrupt:
            print("EXIT")
            exit()
        except Exception as e:
            print(f"[bold red]ERROR: {e}[/bold red]")

    return wrapper


def print_datetime(func):
    def wrapper(*args, **kwargs):
        d = datetime.datetime.now()
        print(d)
        func(*args, **kwargs)

    return wrapper


def get_version():
    try:
        version_str = version(__package__)
    except Exception:
        version_str = "undefined"
    return f"Version: '{ version_str }', package: {__package__}"


# for i in progressbar(range(100), redirect_stdout=True):
#     print("Some text", i)
#     sleep(0.1)


@exception_keyboard
def scan_file_dir(
    output_dir: str,
    im_file_path: str = None,
    im_dir: str = None,
    parameters: dict = {},
    debug: bool = False,
):
    VALID_FORMATS = (".jpg", ".jpeg", ".jp2", ".png", ".bmp", ".tiff", ".tif")

    path_out = Path(output_dir)
    if not path_out.exists():
        path_out.mkdir()

    # Scan single image specified by command line argument --image <IMAGE_PATH>
    if im_file_path:
        im_file = Path(im_file_path)
        if im_file.suffix.lower() not in VALID_FORMATS:
            print(f"[bold red]File '{im_file_path}' not is {VALID_FORMATS}[/bold red]")
            return

        if im_file.exists() and im_file.is_file():
            im_scan(im_file, path_out, parameters=parameters, debug=debug)
        else:
            print(f"[bold red]File '{im_file_path}' not found[/bold red]")
            return

    # Scan all valid images in directory specified by command line argument --images <IMAGE_DIR>
    else:
        path_in = Path(im_dir)
        if not path_in.exists():
            print(f"[bold red]Folder '{im_dir}' not found[/bold red]")
            return

        im_files = path_in.glob("*.*")

        im_files = list(
            filter(lambda f: f.suffix.lower() in VALID_FORMATS, path_in.glob("*.*"))
        )

        output_files = path_in.glob("*.*")

        output_files = list(
            filter(lambda f: f.suffix.lower() in VALID_FORMATS, path_out.glob("*.*"))
        )

        im_files_not_pass = []
        for i in im_files:
            is_found = False
            for ind, o in enumerate(output_files):
                if i.name == o.name:
                    output_files.pop(ind)
                    is_found = True
                    break
            if not is_found:
                im_files_not_pass.append(i)

        im_files_not_pass = sorted(list(im_files_not_pass))

        total_files = len(im_files)
        total_files_not_pass = len(im_files_not_pass)
        print(
            f"total input files: {total_files}, ready for operations: {total_files_not_pass}"
        )
        wrong = []
        for i in progressbar(range(total_files_not_pass), redirect_stdout=True):
            im = im_files_not_pass[i]
            # print(f"{i}. im_scan({im})")
            if im.is_file():
                result = im_scan(
                    im,
                    path_out,
                    parameters=parameters,
                )
                if not result:
                    wrong.append(im)
        if wrong:
            wrong_total = len(wrong)
            print(f"[yellow]Total SKIPPED files: {wrong_total}[/yellow]")


def app_arg():
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--images", help="Directory of images to be scanned")
    group.add_argument("--image", help="Path to single image to be scanned")
    ap.add_argument(
        "--output",
        default="output",
        help="Path to output result images, default: 'output'",
    )
    ap.add_argument(
        "--gamma",
        default="7.0",
        help="Gamma image correction, default: '7.0'",
    )
    ap.add_argument(
        "--ratio",
        default="1.294",
        help="desired image aspect ratio correction W to H, default: '1.294'",
    )
    ap.add_argument(
        "--debug",
        action="store_true",
        help="debug, CV operation for single image only",
    )
    ap.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="show version",
    )
    args = ap.parse_args()

    # print(args)
    return args


def cli():
    args = app_arg()
    if args.version:
        print(get_version())
        return

    parameters = {"gamma": float(args.gamma), "ratio": float(args.ratio)}
    scan_file_dir(
        args.output, args.image, args.images, parameters=parameters, debug=args.debug
    )
    d = datetime.datetime.now()
    print(d)


if __name__ == "__main__":
    cli()
