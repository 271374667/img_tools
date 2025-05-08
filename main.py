import typer
from pathlib import Path
from PIL import Image
from enum import Enum
import concurrent.futures
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Rotation(str, Enum):
    """Enum for target rotation orientation."""

    HORIZONTAL = "horizontal"  # Renamed from LANDSCAPE
    VERTICAL = "vertical"  # Renamed from PORTRAIT


class ImageUtils:
    """Utility class for image operations."""

    @staticmethod
    def rotate_img(img_path: Path, rotation: Rotation, override: bool) -> Path | None:
        """
        Rotates an image based on the target orientation.

        Args:
            img_path: Path to the input image.
            rotation: The target orientation (Rotation.HORIZONTAL or Rotation.VERTICAL).
            override: If True, overwrites the original image. Otherwise, saves
                      with '_out' suffix.

        Returns:
            The path to the processed image, or None if an error occurred.
            Returns the original path if no rotation was needed.
        """
        try:
            img = Image.open(img_path)
            width, height = img.size
            needs_rotation = False

            # Determine if rotation is needed based on new enum names
            if rotation == Rotation.HORIZONTAL and height > width:
                needs_rotation = True
                logger.debug(
                    f"Image {img_path.name} is vertical, needs rotation to horizontal."
                )
            elif rotation == Rotation.VERTICAL and width > height:
                needs_rotation = True
                logger.debug(
                    f"Image {img_path.name} is horizontal, needs rotation to vertical."
                )
            else:
                logger.debug(
                    f"Image {img_path.name} already matches target orientation '{rotation.value}'. No rotation needed."
                )

            if needs_rotation:
                # Rotate 90 degrees clockwise. Adjust if a different rotation is desired.
                # Use transpose(Image.Transpose.ROTATE_270) for PIL versions >= 8.0.0
                # Use transpose(Image.ROTATE_270) for older versions
                try:
                    rotated_img = img.transpose(Image.Transpose.ROTATE_270)
                except AttributeError:  # Fallback for older Pillow versions
                    rotated_img = img.transpose(Image.ROTATE_270)
                logger.info(f"Rotating {img_path.name} to {rotation.value}...")

                # Preserve EXIF data if present
                exif = img.info.get("exif")

                # Determine output path
                if override:
                    output_path = img_path
                    logger.debug(f"Output path (override): {output_path}")
                else:
                    output_path = img_path.with_name(
                        f"{img_path.stem}_out{img_path.suffix}"
                    )
                    logger.debug(f"Output path (new file): {output_path}")

                # Close original image before saving (especially important for override)
                img.close()

                # Save the rotated image
                save_kwargs = {}
                if exif:
                    save_kwargs["exif"] = exif
                rotated_img.save(output_path, **save_kwargs)
                rotated_img.close()
                logger.info(f"Saved rotated image to {output_path}")
                return output_path
            else:
                # No rotation needed
                img.close()
                # Return original path signify processing completed, even if no change.
                return img_path

        except FileNotFoundError:
            logger.error(f"Error: Image file not found at {img_path}")
            return None
        except Exception as e:
            logger.error(f"Error processing image {img_path.name}: {e}")
            # Ensure image is closed if opened before error
            try:
                if "img" in locals() and img.fp:
                    img.close()
                if (
                    "rotated_img" in locals()
                    and hasattr(rotated_img, "fp")
                    and rotated_img.fp
                ):
                    rotated_img.close()
            except Exception as close_e:
                logger.error(
                    f"Error closing image file {img_path.name} during error handling: {close_e}"
                )
            return None


# Create the main Typer application
app = typer.Typer()


# Add the rotate command to the 'img' group
@app.command("rotate")
def rotate_images_cli(
    img_dir: Path = typer.Argument(
        ...,  # Required argument
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        help="Directory containing images to rotate.",
    ),
    rotation: Rotation = typer.Option(
        Rotation.VERTICAL,  # Default rotation is Vertical
        "--rotation",
        "-r",
        case_sensitive=False,
        help="Target orientation: 'horizontal' or 'vertical'.",
    ),
    img_suffix: str = typer.Option(
        "png",
        "--suffix",
        "-s",
        help="Image file suffix (without dot) to search for.",
    ),
    override: bool = typer.Option(
        True,  # Default value is True (override original)
        "--override/--no-override",
        "-o/-no",
        help="Overwrite original images instead of creating '_out' copies.",
    ),
    max_workers: int = typer.Option(
        None,  # Default to None, ThreadPoolExecutor will decide
        "--workers",
        "-w",
        help="Maximum number of worker threads. Defaults to Python's default.",
    ),
):
    """
    Rotates images in a directory to the target orientation (default: vertical)
    using multiple threads.
    """
    logger.info("Starting image rotation process...")
    logger.info(f"Source Directory: {img_dir}")
    logger.info(f"Target Orientation: {rotation.value}")
    logger.info(f"Image Suffix: .{img_suffix}")
    logger.info(f"Override Originals: {override}")
    logger.info(f"Max Workers: {'Default' if max_workers is None else max_workers}")

    # Find images recursively
    image_pattern = f"*.{img_suffix.lstrip('.')}"
    logger.info(f"Searching for '{image_pattern}' files in {img_dir}...")
    image_paths = list(img_dir.rglob(image_pattern))

    if not image_paths:
        logger.warning(f"No images found with suffix '.{img_suffix}' in {img_dir}.")
        print(f"No images found with suffix '.{img_suffix}' in {img_dir}.")
        raise typer.Exit()

    logger.info(f"Found {len(image_paths)} images to process.")
    print(f"Found {len(image_paths)} images to process.")

    processed_count = 0
    error_count = 0
    utils = ImageUtils()  # Instantiate the utility class

    # Use ThreadPoolExecutor for parallel processing
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks
        futures = {
            executor.submit(utils.rotate_img, img_path, rotation, override): img_path
            for img_path in image_paths
        }

        # Process completed tasks with tqdm progress bar
        try:
            with tqdm(total=len(futures), desc="Rotating images", unit="img") as pbar:
                for future in concurrent.futures.as_completed(futures):
                    img_path = futures[future]
                    try:
                        result_path = future.result()
                        if result_path:
                            processed_count += 1
                            # Log success only at debug level to avoid clutter
                            logger.debug(
                                f"Successfully processed {img_path.name}. Output/Final state: {result_path}"
                            )
                        else:
                            error_count += 1
                            logger.warning(
                                f"Skipped {img_path.name} due to processing error."
                            )
                    except Exception as exc:
                        error_count += 1
                        logger.error(
                            f"Image {img_path.name} generated an exception during future retrieval: {exc}"
                        )
                    finally:
                        pbar.update(1)  # Update progress bar
        except KeyboardInterrupt:
            logger.warning("Process interrupted by user. Shutting down workers...")
            print("\nProcess interrupted. Waiting for active tasks to finish...")
            # Optional: Cancel pending futures if desired
            # for future in futures:
            #     if not future.done(): future.cancel()
            concurrent.futures.wait(
                futures, return_when=concurrent.futures.ALL_COMPLETED
            )
            logger.info("Workers shut down.")
            print("Exiting.")
            raise typer.Exit(code=1)

    logger.info("Image rotation process finished.")
    print("\n--- Processing Summary ---")
    print(f"Total images found: {len(image_paths)}")
    print(f"Successfully processed/checked: {processed_count}")
    print(f"Errors encountered: {error_count}")
    print("-------------------------")


if __name__ == "__main__":
    # TODO: 图片水印
    # TODO: 图片上色
    app()
