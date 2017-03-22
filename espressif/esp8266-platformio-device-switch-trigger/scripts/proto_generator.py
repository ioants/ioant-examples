import ioant.proto as proto
Import("env")


def before_build():
    print "before_build"
    # do some actions


def after_build():
    print "after_build"


env.AddPreAction("$BUILD_DIR/src/main.cpp", before_build)
env.AddPostAction("$BUILD_DIR/src/main.cpp", after_build)

# proto.embedded_main(output_dir)
proto.embedded_main("lib/generated_proto/")
print "Current build targets", map(str, BUILD_TARGETS)
