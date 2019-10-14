import fcntl
import mmap
import os
import tempfile
import threading
import typing
from pathlib import Path

#import ctypes

__all__ = ("MempipedPathRead", "MempipedPathWrite", "MempipedPathTmp")

currentProcProcFs = Path("/proc") / str(os.getpid())
currentProcFileDescriptors = currentProcProcFs / "fd"
currentProcMmaps = currentProcProcFs / "maps"


class MempipedPathBase:
	__slots__ = ("pO", "pI", "data")

	def __init__(self):
		self.pO = None
		self.pI = None
		self.data = None

	def __enter__(self) -> Path:
		self.pO, self.pI = os.pipe()


try:
	raise Exception("Fuck, this causes the process to enter `D uninterruptible sleep` state")
	import errno
	import stat
	from datetime import datetime

	import fuse

	fuse.fuse_python_api = (0, 2)

	class MempipedPathFuseOps(fuse.Fuse):
		__slots__ = ("buffer", "datetime", "mode")
		fileName = "MempipedPath"

		def __init__(self, buffer, mode=0o755, *args, **kwargs):
			super().__init__(*args, **kwargs)
			self.buffer = buffer
			self.datetime = int(datetime.now().timestamp())
			self.mode = mode

		def read(self, path, length, offset):
			return self.buffer[offset:length]

		def write(self, path, buf, offset):
			self.buffer[offset : size(buf)] = buf

		def ftruncate(self, length):
			self.buffer = self.buffer[:length]

		def getattr(self, path):
			st = fuse.Stat()

			st.st_mtime = self.datetime
			st.st_ctime = self.datetime
			st.st_atime = self.datetime
			st.st_size = len(self.buffer)
			st.st_nlink = 2
			self.st_uid = os.geteuid()
			self.st_gid = os.getgid()

			if path == "/":
				st.st_mode = stat.S_IFDIR | self.mode
			else:
				st.st_mode = stat.S_IFREG | self.mode

			return st

		def readdir(self, path, offset):
			yield fuse.Direntry(self.__class__.fileName)

		def open(self, path, flags):
			pass

	class MempipedPathReadFUSE:
		"""Allows you to feed a buffer to badly written external program/libss reading a file on a disk only"""

		__slots__ = ("data", "thread", "tmpDir")

		def __init__(self, data: typing.Union[str, bytes]):
			if isinstance(data, str):
				data = data.encode("utf-8")
			self.tmpDir = None

		def __enter__(self) -> Path:
			self.tmpDir = tempfile.TemporaryDirectory(suffix=None, prefix=None, dir=".")

			def threadF():
				server = MempipedPathFuseOps(self.data)
				server.fuse_args.setmod("foreground")
				server.fuse_args.mountpoint = self.tmpDir.name
				server.main()

			self.thread = threading.Thread(target=threadF)
			self.thread.start()
			return Path(self.tmpDir.name) / MempipedPathFuseOps.fileName

		def __exit__(self, *args, **kwargs):
			self.thread.join()
			self.tmpDir.cleanup()

	__all__.append("MempipedPathReadFUSE")
except:
	pass


class MempipedPathTmp:
	"""Allows you to feed a buffer to badly written external program/libss reading a file on a disk only. This uses a real temporary file. Can capture both read and written data. But FS is involved."""

	__slots__ = ("data", "tmpFile", "file", "tmpFileHandle", "write", "read")

	def __init__(self, data: typing.Union[str, bytes], read=True, write=False):
		if isinstance(data, str):
			data = data.encode("utf-8")
		self.data = data
		self.read = read
		self.write = write
		assert read or write

	def __enter__(self) -> Path:
		self.tmpFile = tempfile.NamedTemporaryFile()
		self.file = Path(self.tmpFile.name)
		if self.read:
			self.tmpFile.truncate(len(self.data))
			with mmap.mmap(self.tmpFile.fileno(), len(self.data)) as tmpFileMapping:
				tmpFileMapping[:] = self.data
		return self

	def __exit__(self, *args, **kwargs):
		if self.write:
			sz = self.file.stat().st_size
			if sz:
				with mmap.mmap(self.tmpFile.fileno(), sz) as tmpFileMapping:
					self.data = bytes(tmpFileMapping)
		self.tmpFile.__exit__(*args, **kwargs)


class MempipedPathRead(MempipedPathBase):
	"""Allows you to feed a buffer to badly written external program/libss reading a file on a disk only. Uses an anonymous pipe."""

	__slots__ = ("thread",)

	def __init__(self, data: typing.Union[str, bytes]):
		super().__init__()
		self.data = data

	def __enter__(self) -> Path:
		super().__enter__()

		def threadF():
			with os.fdopen(self.pI, "w" + ("b" if isinstance(self.data, bytes) else "")) as pIF:
				pIF.write(self.data)
				pIF.flush()

		self.thread = threading.Thread(target=threadF)
		self.thread.start()
		return currentProcFileDescriptors / str(self.pO)

	def __exit__(self, *args, **kwargs):
		self.thread.join()
		os.close(self.pO)
		try:
			os.close(self.pI)
		except BaseException:
			pass


class MempipedPathWrite(MempipedPathBase):
	"""Allows you to capture the buffer that is only saved into a file by a badly written 3rd-party app/lib into a var without using disk. Instead an anonymous pipe is used."""

	__slots__ = ("pOF", "file")

	def __init__(self):
		super().__init__()
		self.data = []

	def __enter__(self) -> Path:
		super().__enter__()
		fcntl.fcntl(self.pO, fcntl.F_SETFL, os.O_NONBLOCK)
		self.pOF = os.fdopen(self.pO, "rb")
		self.file = currentProcFileDescriptors / str(self.pO)
		return self

	def captureIter(self):
		chunk = self.pOF.read()
		if chunk:
			self.data.append(chunk)

	def capture(self, isAlive):
		while isAlive():
			self.captureIter()

	def __exit__(self, *args, **kwargs):
		self.file = None
		self.pOF.close()
		os.close(self.pI)
		try:
			os.close(self.pO)
		except BaseException:
			pass
		self.data = b"".join(self.data)
