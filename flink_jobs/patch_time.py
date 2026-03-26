import re
with open("log_processor.py", "r") as f: s = f.read()
s = s.replace("TumblingEventTimeWindows.of", "TumblingProcessingTimeWindows.of")
s = s.replace("SlidingEventTimeWindows.of", "SlidingProcessingTimeWindows.of")
s = s.replace("from pyflink.datastream.window import TumblingEventTimeWindows, SlidingEventTimeWindows", "from pyflink.datastream.window import TumblingEventTimeWindows, SlidingEventTimeWindows, TumblingProcessingTimeWindows, SlidingProcessingTimeWindows")
with open("log_processor.py", "w") as f: f.write(s)
