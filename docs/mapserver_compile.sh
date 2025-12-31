# Needs gcc/g++/cmake/swig provided by conda-forge, maybe
# Needs older sysroot-linux=2.17

export PREFIX=/opt/miniconda3/envs/prod
# export LD_LIBRARY_PATH=/opt/miniconda3/envs/prod/lib:$LD_LIBRARY_PATH
export PKG_CONFIG_LIBDIR=$PREFIX/lib

# Note, mapserver-sample.conf goes to /etc/opt/ per 
# https://cmake.org/cmake/help/latest/module/GNUInstallDirs.html
cmake .. \
-DBUILD_FUZZER_REPRODUCER=OFF \
-DBUILD_TESTING=OFF \
-DMAPSERVER_CONFIG_FILE=$PREFIX/etc/mapserver.conf \
-DCMAKE_INSTALL_PREFIX:PATH=$PREFIX \
-DCMAKE_INSTALL_LIBDIR=lib \
-DWITH_CLIENT_WFS=1 \
-DWITH_CLIENT_WMS=1 \
-DWITH_GIF=1 \
-DWITH_PHPNG=1 \
-DPHP_EXTENSION_DIR=/usr/lib64/php/modules \
-DWITH_PYTHON=1 \
-DWITH_PROTOBUFC=0 \
-DWITH_FRIBIDI=1 \
-DWITH_FCGI=1 \
-DWITH_PCRE2=OFF \
-DCMAKE_INSTALL_PREFIX:PATH=$PREFIX \
-DPNG_LIBRARY=$PREFIX/lib/libpng.so \
-DPNG_INCLUDE_DIR=$PREFIX/include \
-DJPEG_LIBRARY=$PREFIX/lib/libjpeg.so \
-DJPEG_INCLUDE_DIR=$PREFIX/include \
-DFREETYPE_LIBRARY=$PREFIX/lib/libfreetype.so \
-DFREETYPE_INCLUDE_DIRS=$PREFIX/include \
-DGIF_LIBRARY=$PREFIX/lib/libgif.so \
-DGIF_INCLUDE_DIR=$PREFIX/include \
-DCAIRO_LIBRARY=$PREFIX/lib/libcairo.so \
-DCAIRO_INCLUDE_DIR=$PREFIX/include/cairo/ \
-DCURL_LIBRARY=$PREFIX/lib/libcurl.so \
-DCURL_INCLUDE_DIR=$PREFIX/include \
-DPROJ_LIBRARY=$PREFIX/lib/libproj.so \
-DPROJ_INCLUDE_DIR=$PREFIX/include \
-DLIBXML2_LIBRARY=$PREFIX/lib/libxml2.so \
-DLIBXML2_INCLUDE_DIR=$PREFIX/include/libxml2/ \
-DHARFBUZZ_LIBRARY=$PREFIX/lib/libharfbuzz.so \
-DHARFBUZZ_INCLUDE_DIR=$PREFIX/include/harfbuzz/ \
-DZLIB_LIBRARY=$PREFIX/lib/libz.so \
-DZLIB_INCLUDE_DIR=$PREFIX/include \
-DGEOS_LIBRARY=$PREFIX/lib/libgeos_c.so \
-DGEOS_INCLUDE_DIR=$PREFIX/include \
-DGDAL_LIBRARY=$PREFIX/lib/libgdal.so \
-DGDAL_INCLUDE_DIR=$PREFIX/include \
-DPostgreSQL_LIBRARY=$PREFIX/lib/libpq.so \
-DPostgreSQL_INCLUDE_DIR=$PREFIX/include

