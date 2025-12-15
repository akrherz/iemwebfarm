#conda create -n ms python=3.6 proj4=5.2.0 libpng=1.6.37 jpeg=9c freetype=2.10.0 giflib=5.1.7 cairo=1.16.0 libcurl=7.65.3 libxml2=2.9.10  harfbuzz=2.4.0 fribidi=1.0.5 zlib=1.2.11 geos=3.7.1 gdal=2.4.1
# conda create -n ms python=3.6 proj4=5.2.0 libpng jpeg freetype giflib cairo libcurl libxml2  harfbuzz fribidi zlib geos gdal
#export PATH=$PATH:/usr/pgsql-12/bin
export PREFIX=/opt/miniconda3/envs/prod

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
-DFREETYPE_INCLUDE_DIR=$PREFIX/include \
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

