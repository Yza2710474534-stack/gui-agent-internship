"""模块测试：只用构造图片和模拟鼠标，不实际操作电脑。"""

import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

import cv2
import numpy as np

from src import controller as control
from src import screen_capture as capture
from src.coordinate import image_to_screen
from src.element_locator import find_icon
from src.ocr_engine import OCREngine
from src.visualizer import draw_target


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.region = dict(left=100, top=50, width=200, height=100)
        self.image = np.zeros((100, 200, 3), np.uint8)

    def test_default_monitor_is_real_screen(self):
        combined = dict(left=0, top=0, width=400, height=100)
        self.assertEqual(capture.select_monitor([combined, self.region]), self.region)

    def test_explicit_monitor_and_invalid_monitor(self):
        self.assertEqual(capture.select_monitor([self.region], 0), self.region)
        with self.assertRaises(ValueError):
            capture.select_monitor([self.region], 2)

    def test_no_screen_is_reported(self):
        with self.assertRaises(RuntimeError):
            capture.select_monitor([dict(left=0, top=0, width=0, height=0)])

    def test_resized_frame_keeps_offset_and_scale(self):
        image, data = capture.prepare_frame(self.image, self.region, (100, 25))
        self.assertEqual(image.shape, (25, 100, 3))
        self.assertEqual(data['scale_to_screen'], [2, 4])
        self.assertEqual(image_to_screen(10, 5, data['image_size'], data['screen_region']), (120, 70))

    def test_bad_output_size(self):
        for size in ((0, 10), (10, -1), (2.5, 10)):
            with self.assertRaises(ValueError):
                capture.prepare_frame(self.image, self.region, size)

    def test_capture_backend_converts_bgra(self):
        tool = Mock(monitors=[self.region])
        tool.grab.return_value = np.full((100, 200, 4), 23, np.uint8)
        with patch('src.screen_capture.mss.MSS') as factory:
            factory.return_value.__enter__.return_value = tool
            image, data = capture.capture_with_metadata()
        self.assertEqual(image.shape, (100, 200, 3))
        self.assertEqual(int(image[0, 0, 0]), 23)
        self.assertEqual(data['image_size'], [200, 100])

    def test_outside_region_never_grabs(self):
        tool = Mock(monitors=[self.region])
        with patch('src.screen_capture.mss.MSS') as factory:
            factory.return_value.__enter__.return_value = tool
            with self.assertRaises(ValueError):
                capture.capture_region(99, 50, 20, 20)
        tool.grab.assert_not_called()

    def test_sequence_saves_three_images_and_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('src.screen_capture.capture_with_metadata', side_effect=lambda *a: capture.prepare_frame(self.image, self.region)):
                records = capture.capture_sequence(3, 0, output_dir=directory)
            self.assertEqual(len({r['path'] for r in records}), 3)
            for record in records:
                path = Path(record['path'])
                self.assertTrue(path.is_file())
                data = json.loads(path.with_suffix('.json').read_text())
                self.assertEqual(data['screen_region'], [100, 50, 200, 100])

    def test_invalid_sequence_stops_before_capture(self):
        with patch('src.screen_capture.capture_with_metadata') as grab:
            for count, interval in ((0, 0), (1001, 0), (1, -1), (1, float('nan'))):
                with self.assertRaises(ValueError):
                    capture.capture_sequence(count, interval)
            grab.assert_not_called()

    def test_save_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as directory, patch('src.screen_capture.cv2.imwrite', return_value=False):
            with self.assertRaises(RuntimeError):
                capture.save_image(self.image, output_dir=directory)


class CoordinateTests(unittest.TestCase):
    def test_various_resolutions_and_retina_simulation(self):
        for width, height in ((1280, 720), (1470, 956), (1920, 1080), (3840, 2160)):
            with self.subTest(resolution=(width, height)):
                self.assertEqual(image_to_screen(width/2, height/2, (width, height), (0, 0, width/2, height/2)), (width/4, height/4))

    def test_negative_screen_offset(self):
        self.assertEqual(image_to_screen(50, 20, (100, 100), (-200, 30, 200, 100)), (-100, 50))

    def test_invalid_coordinates_and_dimensions(self):
        for x, y, size in ((-1, 0, (10, 10)), (10, 0, (10, 10)), (0, float('inf'), (10, 10)), (0, 0, (0, 10))):
            with self.assertRaises(ValueError):
                image_to_screen(x, y, size, (0, 0, 10, 10))


class OCRTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'sample.png'
        cv2.imwrite(str(self.path), np.zeros((40, 100, 3), np.uint8))
        self.engine = OCREngine.__new__(OCREngine)
        self.engine.reader = Mock()
        box = [[30, 6], [90, 6], [90, 30], [30, 30]]
        self.engine.reader.readtext.return_value = [(box, '编辑', .98), (box, '错误', .1)]

    def test_ocr_coordinates_restore_to_input_image(self):
        data = self.engine.recognize(self.path)
        self.assertEqual(data['items'][0]['center'], [20, 6])
        self.assertEqual(data['items'][0]['bbox'][0], [10, 2])
        self.assertEqual(data['image_size'], [100, 40])
        self.assertEqual(self.engine.reader.readtext.call_args.args[0].shape, (120, 300, 3))

    def test_low_confidence_is_separated(self):
        data = self.engine.recognize(self.path)
        self.assertEqual([v['text'] for v in data['items']], ['编辑'])
        self.assertEqual([v['text'] for v in data['low_confidence_items']], ['错误'])

    def test_missing_image(self):
        with self.assertRaises(ValueError):
            self.engine.recognize(self.path.with_name('missing.png'))
        self.engine.reader.readtext.assert_not_called()

    def test_bad_confidence_and_scale(self):
        for confidence, scale in ((-1, 3), (1.1, 3), (float('nan'), 3), (.3, 0), (.3, 2.5)):
            with self.assertRaises(ValueError):
                self.engine.recognize(self.path, confidence, scale)


class ElementTests(unittest.TestCase):
    def setUp(self):
        self.template = np.random.default_rng(7).integers(0, 256, (12, 12, 3), dtype=np.uint8)
        self.image = np.zeros((80, 120, 3), np.uint8)

    def test_icon_location(self):
        self.image[20:32, 30:42] = self.template
        result = find_icon(self.image, self.template)
        self.assertEqual(result['center'], [35.5, 25.5])
        self.assertGreater(result['confidence'], .99)

    def test_scaled_icon(self):
        self.image[20:44, 30:54] = cv2.resize(self.template, (24, 24))
        result = find_icon(self.image, self.template, scales=(1, 2))
        self.assertEqual(result['template_scale'], 2)
        self.assertEqual(result['center'], [41.5, 31.5])

    def test_absent_icon_returns_none(self):
        self.assertIsNone(find_icon(self.image, self.template))

    def test_flat_template_is_rejected(self):
        with self.assertRaises(ValueError):
            find_icon(self.image, np.zeros_like(self.template))

    def test_visualization_draws_without_changing_original(self):
        self.image[20:32, 30:42] = self.template
        original = self.image.copy()
        item = find_icon(self.image, self.template)
        marked, matches = draw_target(self.image, [item], '模板图标')
        np.testing.assert_array_equal(self.image, original)
        np.testing.assert_array_equal(marked[26, 36], [0, 0, 255])
        np.testing.assert_array_equal(marked[20, 30], [0, 255, 0])
        self.assertEqual(len(matches), 1)

    def test_bad_box_and_missing_target(self):
        with self.assertRaises(ValueError):
            draw_target(self.image, [], '编辑')
        with self.assertRaises(ValueError):
            draw_target(self.image, [{'text': '编辑', 'bbox': [], 'center': [0, 0]}], '编辑')


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.mouse = Mock()
        self.mouse.size.return_value = (1470, 956)
        self.mouse.position.return_value = (100, 100)
        patcher = patch('src.controller._mouse', return_value=self.mouse)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_move_and_click(self):
        control.move_to(200, 100)
        control.click(200, 100)
        self.mouse.moveTo.assert_called_once_with(200, 100, duration=.5)
        self.mouse.click.assert_called_once_with(200, 100, button='left')

    def test_bad_position_never_clicks(self):
        for point in ((1470, 0), (-1, 20), (10, float('nan'))):
            with self.assertRaises(ValueError):
                control.click(*point)
        self.mouse.click.assert_not_called()

    def test_english_input(self):
        control.type_text('Hello GUI Agent')
        self.mouse.write.assert_called_once_with('Hello GUI Agent', interval=.1)

    def test_unsupported_text_never_types(self):
        with self.assertRaises(ValueError):
            control.type_text('你好')
        self.mouse.write.assert_not_called()

    def test_scroll_both_directions(self):
        control.scroll(3)
        control.scroll(-3)
        self.assertEqual([c.args[0] for c in self.mouse.scroll.call_args_list], [3, -3])

    def test_bad_scroll_and_duration(self):
        with self.assertRaises(ValueError):
            control.scroll(1.5)
        with self.assertRaises(ValueError):
            control.move_to(10, 10, -1)
        with self.assertRaises(ValueError):
            control.drag_to(10, 10, 0)

    def test_nonmac_drag_releases_on_failure(self):
        self.mouse.dragTo.side_effect = RuntimeError('模拟中断')
        with patch('src.controller.sys.platform', 'win32'), self.assertRaises(RuntimeError):
            control.drag_to(200, 200)
        self.mouse.platformModule._mouseUp.assert_called_once_with(100, 100, 'left')

    def test_nonmac_drag_normal(self):
        with patch('src.controller.sys.platform', 'linux'):
            control.drag_to(200, 200)
        self.mouse.dragTo.assert_called_once_with(200, 200, duration=2.0, button='left')
        self.mouse.platformModule._mouseUp.assert_called_once()

    def test_mac_drag_releases_on_interruption(self):
        quartz = Mock()
        quartz.kCGEventLeftMouseDown = 1
        quartz.kCGEventLeftMouseDragged = 6
        quartz.kCGEventLeftMouseUp = 2
        event = object()
        quartz.CGEventCreateMouseEvent.return_value = event
        self.mouse.failSafeCheck.side_effect = [None, RuntimeError('模拟紧急停止')]
        with patch.dict('sys.modules', {'Quartz': quartz}), patch('src.controller.sys.platform', 'darwin'), patch('src.controller.time.sleep'):
            with self.assertRaises(RuntimeError):
                control.drag_to(200, 200)
        quartz.CGEventSetType.assert_called_with(event, 2)
        self.assertEqual(quartz.CGEventPost.call_count, 2)

    def test_mac_drag_posts_full_sequence(self):
        quartz = Mock()
        quartz.kCGEventLeftMouseUp = 2
        with patch.dict('sys.modules', {'Quartz': quartz}), patch('src.controller.sys.platform', 'darwin'), patch('src.controller.time.sleep'):
            control.drag_to(200, 200)
        self.assertEqual(quartz.CGEventPost.call_count, 62)
        quartz.CGEventSetLocation.assert_called_with(quartz.CGEventCreateMouseEvent.return_value, (200, 200))


if __name__ == '__main__':
    unittest.main()
